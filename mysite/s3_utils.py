from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    location='media'
    file_overwrite=False 
    default_acl='public-read'

class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True
    gzip = True
    # Set 1 year cache
    querystring_auth = False
    headers = {
        'Cache-Control': 'max-age=31536000, public'
    }    