
import io
import boto3

from app.core.config import settings


class S3StorageService:

    def __init__(self):

        # Boto3 automatically finds AWS credentials from:
        # 1. Environment variables
        # 2. AWS credentials file
        # 3. IAM role attached to AWS services
        self.s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            use_ssl=True,
        )

        self.bucket = settings.AWS_S3_BUCKET

    def upload_file(
        self,
        file_bytes: bytes,
        object_key: str,
        content_type: str,
    ) -> None:

        if not file_bytes:
            raise ValueError("File cannot be empty")

        if not isinstance(object_key, str) or not object_key.strip():
            raise ValueError("Invalid object key")

        if content_type != "application/pdf":
            raise ValueError("Unsupported content type")

        self.s3.upload_fileobj(
            Fileobj=io.BytesIO(file_bytes),
            Bucket=self.bucket,
            Key=object_key,
            ExtraArgs={
                "ContentType": content_type,
                "ServerSideEncryption": (
                    settings.S3_SERVER_SIDE_ENCRYPTION
                ),
            },
        )

    def download_file(self, object_key: str) -> bytes:

        response = self.s3.get_object(
            Bucket=self.bucket,
            Key=object_key,
        )

        return response["Body"].read()

    def delete_file(self, object_key: str) -> None:

        self.s3.delete_object(
            Bucket=self.bucket,
            Key=object_key,
        )
