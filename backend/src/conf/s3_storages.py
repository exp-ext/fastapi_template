from src.conf import settings
from src.conf.s3_client import S3StorageManager


class MediaStorage(S3StorageManager):
    bucket_name = settings.MINIO_MEDIA_BUCKET
    default_acl = 'public-read'
    # custom_domain = '{}.{}'.format(bucket_name, settings.MINIO_DOMAIN)


class DatabaseStorage(S3StorageManager):
    bucket_name = settings.MINIO_DATABASE_BUCKET
    default_acl = 'private'


media_storage = MediaStorage()
database_storage = DatabaseStorage()
