import os

from django.core.exceptions import ValidationError


def allow_only_image_validator(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".png", ".jpg", ".jpeg"]
    if ext.lower() not in valid_extensions:
        raise ValidationError("unsupported files")
    max_file_size = 2 * 1024 * 1024  # 2MB in bytes
    if value.size >= max_file_size:
        raise ValidationError("File size exceeds 5MB limit.")
