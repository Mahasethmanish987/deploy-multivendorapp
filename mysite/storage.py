from django.core.files.storage import get_storage_class
from django.contrib.staticfiles.storage import ManifestFilesMixin

class S3ManifestStaticStorage(ManifestFilesMixin, get_storage_class('mysite.s3_utils.StaticStorage')):
    pass