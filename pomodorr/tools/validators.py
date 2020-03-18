from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image(file_object):
    file_size = file_object.size
    max_size = settings.MAX_UPLOAD_SIZE
    if file_size > max_size:
        raise ValidationError("The file size have been exceeded. Max file size is %sMB" % str(max_size/1024/1024))
