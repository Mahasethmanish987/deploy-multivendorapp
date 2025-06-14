from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage,S3StaticStorage 

class MediaStorage(S3Boto3Storage):
    default_acl='private'
    file_overwrite=False 
    location='media'


class StaticStorage(S3StaticStorage):
   default_acl='public-read'
   file_overwite=False 
   location='static'