"""S3 related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3ServiceResource
else:
    S3ServiceResource = Any


# Define a stub class that mimics the real S3Path interface
class S3PathStub:
    """Stub class in case s3 extras aren't installed."""

    @classmethod
    def from_uri(cls, image_path: str) -> S3PathStub:
        """Throw an error if we try to initialize the stub class."""
        raise ImportError("s3 extras need to be installed")


# Try to import the real S3Path class if available
try:
    from s3path import S3Path
except ImportError:
    # Use the stub class as a fallback
    S3Path = S3PathStub


def s3_resource(role_arn: str | None = None) -> S3ServiceResource:
    """Initialize s3 resource using role."""
    try:
        import boto3
    except ImportError:
        raise ImportError("s3 extras need to be installed")

    if role_arn is not None:
        sts_client = boto3.client("sts")
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn, RoleSessionName=role_arn
        )
        credentials = assumed_role["Credentials"]
        return boto3.resource(
            "s3",
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )
    else:
        return boto3.resource("s3")


__all__ = ["S3Path", "s3_resource"]
