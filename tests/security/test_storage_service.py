
from unittest.mock import Mock

from app.services.storage_service import S3StorageService


def test_delete_file_calls_s3_delete_object():

    storage = S3StorageService.__new__(S3StorageService)

    storage.s3 = Mock()
    storage.bucket = "test-bucket"

    storage.delete_file("documents/test.pdf")

    storage.s3.delete_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="documents/test.pdf"
    )


def test_upload_file_calls_s3_upload_fileobj():

    storage = S3StorageService.__new__(S3StorageService)

    storage.s3 = Mock()
    storage.bucket = "test-bucket"

    file_content = b"%PDF-1.4 test content"

    storage.upload_file(
        file_bytes=file_content,
        object_key="documents/test.pdf",
        content_type="application/pdf",
    )

    storage.s3.upload_fileobj.assert_called_once()

    call_args = storage.s3.upload_fileobj.call_args

    uploaded_file = call_args.kwargs["Fileobj"]

    assert uploaded_file.read() == file_content
    assert call_args.kwargs["Bucket"] == "test-bucket"
    assert call_args.kwargs["Key"] == "documents/test.pdf"

    assert call_args.kwargs["ExtraArgs"] == {
        "ContentType": "application/pdf",
        "ServerSideEncryption": "AES256",
    }


def test_download_file_returns_file_bytes():

    storage = S3StorageService.__new__(S3StorageService)

    storage.s3 = Mock()
    storage.bucket = "test-bucket"

    expected_content = b"%PDF-1.4 test content"

    mock_body = Mock()
    mock_body.read.return_value = expected_content

    storage.s3.get_object.return_value = {
        "Body": mock_body
    }

    result = storage.download_file("documents/test.pdf")

    assert result == expected_content

    storage.s3.get_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="documents/test.pdf",
    )


from unittest.mock import Mock, patch

from app.services.storage_service import S3StorageService


@patch("app.services.storage_service.boto3.client")
def test_s3_storage_service_initialization(mock_boto_client):

    mock_s3 = Mock()
    mock_boto_client.return_value = mock_s3

    with patch("app.services.storage_service.settings.AWS_REGION", "eu-north-1"):
        with patch(
            "app.services.storage_service.settings.AWS_S3_BUCKET",
            "healthguard-test-bucket",
        ):
            storage = S3StorageService()

    mock_boto_client.assert_called_once_with(
        "s3",
        region_name="eu-north-1",
        use_ssl=True,
    )

    assert storage.s3 == mock_s3
    assert storage.bucket == "healthguard-test-bucket"
