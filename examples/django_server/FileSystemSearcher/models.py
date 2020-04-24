from django.db import models

# 
class FileInfo(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    hostname = models.CharField(blank=True, verbose_name='hostnames', max_length=128)
    volume   = models.CharField(verbose_name='volumes', max_length=64)
    file_name = models.CharField(blank=True, verbose_name='file_names', max_length=4096)
    relative_path = models.CharField(verbose_name='relative_paths', max_length=4096)
    full_path = models.CharField(verbose_name='full_paths', max_length=4096)
    size = models.BigIntegerField(verbose_name='sizes')
    dropbox_hash = models.CharField(blank=True, verbose_name='dropbox_hashes', max_length=64, db_index=True)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    suffix = models.CharField(blank=True, verbose_name='suffixes', max_length=64)
    mime_type = models.CharField(blank=True, verbose_name='mime_types', max_length=128)
    mime_encoding = models.CharField(blank=True, verbose_name='mime_encodings', max_length=128)
    is_archive = models.BooleanField(default=False, verbose_name='are archives')

