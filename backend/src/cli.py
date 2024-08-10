import asyncio
import gzip
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import aioboto3
import aiofiles
import typer
from dotenv import load_dotenv
from src.conf import settings

load_dotenv()

app = typer.Typer()
logging.basicConfig(level="INFO")
logger = logging.getLogger()


class S3Manager:
    def __init__(self):
        self.bucket = settings.MINIO_MEDIA_BUCKET
        self.prefix = "backup/"
        self.endpoint_domain = settings.MINIO_DOMAIN
        self.session = aioboto3.Session(
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION_NAME
        )
        self.endpoint_url = self._get_endpoint_url()

    def _get_endpoint_url(self) -> str:
        if self.endpoint_domain.startswith("http"):
            raise ValueError("settings.MINIO_DOMAIN should not start with 'http' or 'https'. Please use just the domain name.")

        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint_domain}"

    async def upload_to_s3(self, source_stream, destination_filename):
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3_client:
            try:
                destination_filename = self.prefix + destination_filename
                await s3_client.upload_fileobj(source_stream, self.bucket, destination_filename)
                logger.info(f"Uploaded {destination_filename} to bucket {self.bucket}")
            except Exception as e:
                logger.error(f"Failed to upload {destination_filename} to bucket {self.bucket}: {e}")
                raise

    async def get_latest_dump_file(self):
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3_client:
            try:
                response = await s3_client.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
                if 'Contents' not in response:
                    raise FileNotFoundError("No backup files found in the bucket.")
                files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
                latest_file = files[0]['Key']
                logger.info(f"Latest dump file found: {latest_file}")
                return latest_file
            except Exception as e:
                logger.error(f"Failed to get latest dump file: {e}")
                raise

    async def download_file_from_s3(self, s3_key, local_path):
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3_client:
            try:
                await s3_client.download_file(self.bucket, s3_key, local_path)
                logger.info(f"Downloaded {s3_key} to {local_path}")
            except Exception as e:
                logger.error(f"Failed to download {s3_key} to {local_path}: {e}")
                raise

    async def delete_old_dumps(self, days=5):
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3_client:
            try:
                response = await s3_client.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
                if 'Contents' not in response:
                    logger.info("No backup files found in the bucket.")
                    return

                now = datetime.now(timezone.utc)
                cutoff_date = now - timedelta(days=days)

                for obj in response['Contents']:
                    last_modified = obj['LastModified']
                    if last_modified < cutoff_date:
                        await s3_client.delete_object(Bucket=self.bucket, Key=obj['Key'])
                        logger.info(f"Deleted {obj['Key']} from bucket {self.bucket}")
            except Exception as e:
                logger.error(f"Failed to delete old dumps: {e}")
                raise


class FileManager:
    @staticmethod
    async def archive_file(source_file, dest_file):
        try:
            async with aiofiles.open(source_file, 'rb') as f_in:
                async with aiofiles.open(dest_file, 'wb') as f_out:
                    async with gzip.GzipFile(fileobj=f_out) as gz_out:
                        await gz_out.write(await f_in.read())
            logger.info(f"Archived {source_file} to {dest_file}")
        except Exception as e:
            logger.error(f"Failed to archive {source_file} to {dest_file}: {e}")
            raise

    @staticmethod
    async def unarchive_file(source_file, dest_file):
        try:
            async with aiofiles.open(source_file, 'rb') as f_in:
                async with aiofiles.open(dest_file, 'wb') as f_out:
                    async with gzip.GzipFile(fileobj=f_in) as gz_in:
                        await f_out.write(await gz_in.read())
            logger.info(f"Unarchived {source_file} to {dest_file}")
        except Exception as e:
            logger.error(f"Failed to unarchive {source_file} to {dest_file}: {e}")
            raise


class DatabaseManager:
    def __init__(self):
        self.s3_manager = S3Manager()

    async def dump_db(self):
        os.environ['PGPASSWORD'] = settings.POSTGRES_PASSWORD
        local_dump_file = 'latest_dump.backup'
        try:
            dump_command = [
                'pg_dump',
                '-h', settings.POSTGRES_HOST,
                '-U', settings.POSTGRES_USER,
                '--section', 'pre-data',
                '--section', 'data',
                '--section', 'post-data',
                '--format', 'custom',
                '--blobs',
                '-f', local_dump_file,
                settings.POSTGRES_DB
            ]
            process = await asyncio.create_subprocess_exec(*dump_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")

            logger.info(f"Database dump completed. File saved as {local_dump_file}")

            await FileManager.archive_file(local_dump_file, local_dump_file + '.gz')

            destination_filename = 'pgsql_' + datetime.strftime(datetime.now(), "%Y.%m.%d.%H:%M") + 'UTC' + '.backup.gz'
            async with aiofiles.open(local_dump_file + '.gz', 'rb') as data:
                await self.s3_manager.upload_to_s3(data, destination_filename)

            logger.info(f"Local dump files {local_dump_file} and {local_dump_file}.gz removed")

            await self.s3_manager.delete_old_dumps()
        except Exception as e:
            logger.error(f"An error occurred during dump_db: {e}")
            raise
        finally:
            if os.path.exists(local_dump_file):
                os.remove(local_dump_file)
            if os.path.exists(local_dump_file + '.gz'):
                os.remove(local_dump_file + '.gz')

    async def terminate_db_connections(self):
        try:
            terminate_command = [
                'psql', '-h', settings.POSTGRES_HOST, '-p', str(settings.POSTGRES_PORT), '-U', settings.POSTGRES_USER, '-d', 'postgres', '-c',
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{settings.POSTGRES_DB}' AND pid <> pg_backend_pid();"
            ]
            terminate_process = await asyncio.create_subprocess_exec(*terminate_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await terminate_process.communicate()
            if terminate_process.returncode != 0:
                logger.error(f"Terminate connections command failed with return code {terminate_process.returncode}")
                logger.error(f"stderr: {stderr.decode()}")
                logger.error(f"stdout: {stdout.decode()}")
                raise Exception(f"Terminate connections failed with return code {terminate_process.returncode}")
            logger.info("Terminated all active connections to the database")
        except Exception as e:
            logger.error(f"An error occurred during terminate_db_connections: {e}")
            raise

    async def drop_and_create_db(self):
        try:
            drop_command = [
                'dropdb', '--if-exists', '-h', settings.POSTGRES_HOST, '-p', str(settings.POSTGRES_PORT), '--username', settings.POSTGRES_USER, settings.POSTGRES_DB
            ]
            drop_process = await asyncio.create_subprocess_exec(*drop_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await drop_process.communicate()
            if drop_process.returncode != 0:
                logger.error(f"dropdb failed with return code {drop_process.returncode}")
                logger.error(f"stderr: {stderr.decode()}")
                logger.error(f"stdout: {stdout.decode()}")
                raise Exception(f"dropdb failed with return code {drop_process.returncode}")
            logger.info("Existing database dropped successfully")

            create_command = [
                'createdb', '-h', settings.POSTGRES_HOST, '-p', str(settings.POSTGRES_PORT), '--username', settings.POSTGRES_USER, settings.POSTGRES_DB
            ]
            create_process = await asyncio.create_subprocess_exec(*create_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await create_process.communicate()
            if create_process.returncode != 0:
                logger.error(f"createdb failed with return code {create_process.returncode}")
                logger.error(f"stderr: {stderr.decode()}")
                logger.error(f"stdout: {stdout.decode()}")
                raise Exception(f"createdb failed with return code {create_process.returncode}")
            logger.info("New database created successfully")
        except Exception as e:
            logger.error(f"An error occurred during drop_and_create_db: {e}")
            raise

    async def restore_db(self, dump_file):
        os.environ['PGPASSWORD'] = settings.POSTGRES_PASSWORD
        try:
            if not os.path.exists(dump_file):
                raise FileNotFoundError(f"The file {dump_file} does not exist")

            await self.terminate_db_connections()
            await self.drop_and_create_db()

            await FileManager.unarchive_file(dump_file, dump_file.replace('.gz', ''))

            async with aiofiles.open(dump_file.replace('.gz', ''), 'rb') as f:
                restore_command = [
                    'pg_restore', '--no-owner', '--dbname',
                    f'postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}'
                ]
                restore_process = await asyncio.create_subprocess_exec(*restore_command, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = await restore_process.communicate()
                if restore_process.returncode != 0:
                    logger.error(f"pg_restore failed with return code {restore_process.returncode}")
                    logger.error(f"stderr: {stderr.decode()}")
                    logger.error(f"stdout: {stdout.decode()}")
                    raise Exception(f"pg_restore failed with return code {restore_process.returncode}")
        except Exception as e:
            logger.error(f"An error occurred during restore_db: {e}")
            raise
        finally:
            if os.path.exists(dump_file.replace('.gz', '')):
                os.remove(dump_file.replace('.gz', ''))

    async def restore_database(self):
        local_dump_file = "latest_dump.backup.gz"
        try:
            latest_dump_s3_key = await self.s3_manager.get_latest_dump_file()
            await self.s3_manager.download_file_from_s3(latest_dump_s3_key, local_dump_file)

            if not os.path.exists(local_dump_file):
                raise FileNotFoundError(f"The downloaded file {local_dump_file} does not exist")

            await self.restore_db(local_dump_file)
            logger.info(f"Database restored successfully from {latest_dump_s3_key}")
        except Exception as e:
            logger.error(f"An error occurred during restore_database: {e}")
            raise
        finally:
            if os.path.exists(local_dump_file):
                os.remove(local_dump_file)


if __name__ == "__main__":
    db_manager = DatabaseManager()
    if len(sys.argv) > 1 and sys.argv[1] == 'restore_database':
        try:
            asyncio.run(db_manager.restore_database())
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == 'dump_db':
        try:
            asyncio.run(db_manager.dump_db())
        except Exception as e:
            logger.error(f"Failed to dump database: {e}")
            sys.exit(1)
    else:
        app()
