import aioboto3
from src.conf import settings


class S3AsyncClient:
    def __init__(self):
        self.endpoint_domain = settings.MINIO_DOMAIN
        self.use_ssl = settings.MINIO_USE_SSL
        self.session = aioboto3.Session(
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION_NAME
        )
        self.endpoint_url = self._get_endpoint_url()
        self._validate_attributes()

    @property
    def client(self):
        return self._s3_client_context_manager()

    def _validate_attributes(self):
        if not hasattr(self, "bucket_name") or not self.bucket_name:
            raise ValueError("The 'bucket_name' attribute is required and cannot be empty.")
        if not hasattr(self, "default_acl") or not self.default_acl:
            raise ValueError("The 'default_acl' attribute is required and cannot be empty.")

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
