from src.conf import settings
import aioboto3


class S3BaseClient:
    def __init__(self):
        self.endpoint_domain = settings.MINIO_DOMAIN
        self.use_ssl = settings.MINIO_USE_SSL
        self.session = aioboto3.Session(
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION_NAME
        )
        self.endpoint_url = self._get_endpoint_url()

    @property
    def client(self):
        return self._s3_client_context_manager()

    def _get_endpoint_url(self) -> str:
        if self.endpoint_domain.startswith("http"):
            raise ValueError("settings.MINIO_DOMAIN should not start with 'http' or 'https'. Please use just the domain name.")

        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint_domain}"

    def _s3_client_context_manager(self):
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            use_ssl=self.use_ssl
        )

    async def __aenter__(self):
        self.s3_client = await self._s3_client_context_manager().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.s3_client.__aexit__(exc_type, exc_val, exc_tb)


class MediaStorage(S3BaseClient):
    bucket_name = settings.MINIO_MEDIA_BUCKET
    default_acl = 'public-read'
    custom_domain = '{}.{}'.format(bucket_name, settings.MINIO_DOMAIN)


media_storage = MediaStorage()
