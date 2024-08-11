import asyncio
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from typing import Type

import aiofiles
import typer
from dotenv import load_dotenv
from src.conf import S3BaseClient, database_storage, settings

load_dotenv()

app = typer.Typer()
logging.basicConfig(level="INFO")
logger = logging.getLogger()


class S3DBManager:
    def __init__(self, storage: Type[S3BaseClient]):
        self.storage = storage
        self.prefix = "backup/"

    async def upload_to_s3(self, source_stream, destination_filename):
        try:
            destination_filename = self.prefix + destination_filename
            async with self.storage.client as client:
                await client.upload_fileobj(source_stream, self.storage.bucket_name, destination_filename)
            logger.info(f"Uploaded {destination_filename} to bucket {self.storage.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to upload {destination_filename} to bucket {self.storage.bucket_name}: {e}")
            raise

    async def get_latest_dump_file(self):
        try:
            async with self.storage.client as client:
                response = await client.list_objects_v2(Bucket=self.storage.bucket_name, Prefix=self.prefix)
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
        try:
            async with self.storage.client as client:
                await client.download_file(self.storage.bucket_name, s3_key, local_path)
            logger.info(f"Downloaded {s3_key} to {local_path}")
        except Exception as e:
            logger.error(f"Failed to download {s3_key} to {local_path}: {e}")
            raise

    async def delete_old_dumps(self, days=5):
        try:
            async with self.storage.client as client:
                response = await client.list_objects_v2(Bucket=self.storage.bucket_name, Prefix=self.prefix)
            if 'Contents' not in response:
                logger.info("No backup files found in the bucket.")
                return

            now = datetime.now(timezone.utc)
            cutoff_date = now - timedelta(days=days)

            for obj in response['Contents']:
                last_modified = obj['LastModified']
                if last_modified < cutoff_date:
                    async with self.storage.client as client:
                        await client.delete_object(Bucket=self.storage.bucket_name, Key=obj['Key'])
                    logger.info(f"Deleted {obj['Key']} from bucket {self.storage.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to delete old dumps: {e}")
            raise


class AsyncFileManager:
    @staticmethod
    async def archive_file(source_file, dest_file):
        try:
            async with aiofiles.open(source_file, 'rb') as f_in:
                async with aiofiles.open(dest_file, 'wb') as f_out:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, shutil.copyfileobj, f_in, f_out)
            logger.info(f"Archived {source_file} to {dest_file}")
        except Exception as e:
            logger.error(f"Failed to archive {source_file} to {dest_file}: {e}")
            raise

    @staticmethod
    async def unarchive_file(source_file, dest_file):
        try:
            async with aiofiles.open(source_file, 'rb') as f_in:
                async with aiofiles.open(dest_file, 'wb') as f_out:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, shutil.copyfileobj, f_in, f_out)
            logger.info(f"Unarchived {source_file} to {dest_file}")
        except Exception as e:
            logger.error(f"Failed to unarchive {source_file} to {dest_file}: {e}")
            raise


class AsyncDatabaseManager:
    def __init__(self):
        self.s3_manager = S3DBManager(database_storage)
        self.DATABASE_HOST = settings.POSTGRES_HOST
        self.DATABASE_NAME = settings.POSTGRES_DB
        self.DATABASE_PORT = settings.POSTGRES_PORT
        self.DATABASE_USER = settings.POSTGRES_USER
        self.DATABASE_PASSWORD = settings.POSTGRES_PASSWORD

    async def dump_db(self):
        os.environ['PGPASSWORD'] = self.DATABASE_PASSWORD
        local_dump_file = 'latest_dump.backup'
        try:
            dump_command = [
                'pg_dump',
                '-h', self.DATABASE_HOST,
                '-U', self.DATABASE_USER,
                '--section', 'pre-data',
                '--section', 'data',
                '--section', 'post-data',
                '--format', 'custom',
                '--blobs',
                '-f', local_dump_file,
                self.DATABASE_NAME
            ]
            process = await asyncio.create_subprocess_exec(
                *dump_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr.decode()}")

            logger.info(f"Database dump completed. File saved as {local_dump_file}")

            await AsyncFileManager.archive_file(local_dump_file, local_dump_file + '.gz')

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
                'psql', '-h', self.DATABASE_HOST, '-p', str(self.DATABASE_PORT), '-U', self.DATABASE_USER, '-d', 'postgres', '-c',
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{self.DATABASE_NAME}' AND pid <> pg_backend_pid();"
            ]
            process = await asyncio.create_subprocess_exec(
                *terminate_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"Terminate connections command failed with return code {process.returncode}")
                logger.error(f"stderr: {stderr}")
                logger.error(f"stdout: {stdout}")
                raise Exception(f"Terminate connections failed with return code {process.returncode}")
            logger.info("Terminated all active connections to the database")
        except Exception as e:
            logger.error(f"An error occurred during terminate_db_connections: {e}")
            raise

    async def drop_and_create_db(self):
        try:
            drop_command = [
                'dropdb', '--if-exists', '-h', self.DATABASE_HOST, '-p', str(self.DATABASE_PORT), '--username', self.DATABASE_USER, self.DATABASE_NAME
            ]
            process = await asyncio.create_subprocess_exec(
                *drop_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"dropdb failed with return code {process.returncode}")
                logger.error(f"stderr: {stderr}")
                logger.error(f"stdout: {stdout}")
                raise Exception(f"dropdb failed with return code {process.returncode}")
            logger.info("Existing database dropped successfully")

            create_command = [
                'createdb', '-h', self.DATABASE_HOST, '-p', str(self.DATABASE_PORT), '--username', self.DATABASE_USER, self.DATABASE_NAME
            ]
            process = await asyncio.create_subprocess_exec(
                *create_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"createdb failed with return code {process.returncode}")
                logger.error(f"stderr: {stderr}")
                logger.error(f"stdout: {stdout}")
                raise Exception(f"createdb failed with return code {process.returncode}")
            logger.info("New database created successfully")
        except Exception as e:
            logger.error(f"An error occurred during drop_and_create_db: {e}")
            raise

    async def restore_db(self, dump_file):
        os.environ['PGPASSWORD'] = self.DATABASE_PASSWORD
        try:
            if not os.path.exists(dump_file):
                raise FileNotFoundError(f"The file {dump_file} does not exist")

            await self.terminate_db_connections()
            await self.drop_and_create_db()

            await AsyncFileManager.unarchive_file(dump_file, dump_file.replace('.gz', ''))

            async with aiofiles.open(dump_file.replace('.gz', ''), 'rb') as f:
                restore_command = [
                    'pg_restore', '--no-owner', '--dbname',
                    f'postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}'
                ]
                process = await asyncio.create_subprocess_exec(
                    *restore_command,
                    stdin=f,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    logger.error(f"pg_restore failed with return code {process.returncode}")
                    logger.error(f"stderr: {stderr}")
                    logger.error(f"stdout: {stdout}")
                    raise Exception(f"pg_restore failed with return code {process.returncode}")
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
    db_manager = AsyncDatabaseManager()
    created_new_loop = False

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            created_new_loop = True

        if len(sys.argv) > 1 and sys.argv[1] == 'restore_database':
            try:
                loop.run_until_complete(db_manager.restore_database())
            except Exception as e:
                logger.error(f"Failed to restore database: {e}")
                sys.exit(1)
        elif len(sys.argv) > 1 and sys.argv[1] == 'dump_db':
            try:
                loop.run_until_complete(db_manager.dump_db())
            except Exception as e:
                logger.error(f"Failed to dump database: {e}")
                sys.exit(1)
        else:
            app()

    finally:
        if created_new_loop:
            loop.close()
