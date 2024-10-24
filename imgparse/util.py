"""Utility functions for parsing metadata."""

from typing import TYPE_CHECKING, Any, Callable

from exifread.classes import IfdTag

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3ServiceResource
else:
    S3ServiceResource = Any


def convert_to_degrees(tag: IfdTag) -> float:
    """Convert the `exifread` GPS coordinate IfdTag object to degrees in float format."""
    degrees = convert_to_float(tag, 0)
    minutes = convert_to_float(tag, 1)
    seconds = convert_to_float(tag, 2)

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def convert_to_float(tag: IfdTag, index: int = 0) -> float:
    """Convert `exifread` IfdTag object to float."""
    return float(tag.values[index].num) / float(tag.values[index].den)


def parse_seq(
    tag: dict[str, dict[str, list[str] | str]],
    type_cast_func: Callable[[str], Any] | None = None,
) -> list[Any]:
    """Parse an XML sequence."""
    seq = tag["rdf:Seq"]["rdf:li"]
    if not isinstance(seq, list):
        seq = [seq]
    if type_cast_func is not None:
        seq = [type_cast_func(item) for item in seq]

    return seq


def s3_resource(role_arn: str | None = None) -> S3ServiceResource:
    """Initialize s3 resource using role."""
    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 must be installed via `s3` extras.")

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
