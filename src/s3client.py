from contextlib import asynccontextmanager

from aiobotocore.session import get_session

from .config import AWS_SECRET_KEY, AWS_ACCESS_KEY


class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            file_url_template: str,
            bucket_name: str
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url
        }
        self.base_file_url = file_url_template.format(bucket_name=bucket_name)
        self.bucket_name = bucket_name
        self.session = get_session()

    def gen_url(self, object_name: str) -> str:
        return f"{self.base_file_url}/{object_name}"

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(
            self,
            file: bytes,
            object_name: str
    ) -> str:
        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file
            )

        return self.gen_url(object_name)


s3_client = S3Client(
    access_key=AWS_ACCESS_KEY,
    secret_key=AWS_SECRET_KEY,
    endpoint_url="https://s3.eu-north-1.amazonaws.com",
    file_url_template="https://{bucket_name}.s3.eu-north-1.amazonaws.com",
    bucket_name="powercup"
)
