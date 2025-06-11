# mysite/s3_utils.py
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    
    @property
    def bucket_name(self):
        return settings.AWS_STORAGE_BUCKET_NAME

class StaticStorage(S3Boto3Storage):
    location = 'static'
    
    @property
    def bucket_name(self):
        return settings.AWS_STORAGE_BUCKET_NAME