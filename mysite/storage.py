import logging

from storages.backends.s3boto3 import S3Boto3Storage
from whitenoise.storage import CompressedManifestStaticFilesStorage


class MediaStorage(S3Boto3Storage):
    default_acl = "private"
    file_overwrite = False
    location = "media"


class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = "public-read"
    file_overwite = False


logger = logging.getLogger(__name__)


class NonStrictManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    def post_process(self, paths, dry_run=False, **options):
        try:
            yield from super().post_process(paths, dry_run, **options)
        except Exception as e:
            if "MissingFileError" in str(type(e)) or "could not be found" in str(e):
                logger.warning(f"Skipping post-processing error: {e}")
                return  # Ignore and continue
            else:
                raise
