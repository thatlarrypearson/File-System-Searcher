from django.forms import ModelForm
from FileSystemSearcher.models import FileInfo
 
class FileInfoForm(ModelForm):
    class Meta:
        model = FileInfo
        fields = ['hostname', 'volume', 'file_name', 'relative_path', 'full_path', 'size',
                    'dropbox_hash', 'suffix', 'mime_type', 'mime_encoding',
                ]