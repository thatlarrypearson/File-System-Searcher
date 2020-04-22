from django.contrib import admin
from .models import FileInfo

admin.site.site_header = "File System Searcher Django Server"

@admin.register(FileInfo)
class FileInfoAdmin(admin.ModelAdmin):
    fields = [
        "hostname",
        "volume",
        "file_name",
        "relative_path",
        "full_path",
        "size",
        "dropbox_hash",
        "created",
        "modified",
        "suffix",
        "mime_type",
        "mime_encoding",
    ]
    readonly_fields = ['id',  ]
    exclude = None



