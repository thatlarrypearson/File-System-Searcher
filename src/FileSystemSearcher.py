# FileSystemSearcher.py
import os
import pytz
import mimetypes
import socket
from pathlib import Path, WindowsPath, PurePath
from platform import uname
from argparse import ArgumentParser
from datetime import datetime
from hashlib import sha256


HASH_BLOCK_SIZE = 4 * 1024 * 1024

def dropbox_hash(path):
    hash_list = []

    with open(path, 'rb') as f:
        while True:
            chunk = f.read(HASH_BLOCK_SIZE)
            if len(chunk) == 0:
                break

            hash_list.append(sha256(chunk).digest())
    
    hash = sha256(b"".join(hash_list))
    return  hash.hexdigest()

def convert_datetime_to_utc(dt):
    return pytz.utc.localize(dt)

# https://docs.python.org/3/library/pathlib.html
# https://docs.python.org/3/library/mimetypes.html
# https://docs.python.org/3/library/csv.html


class Crawler():
    def __init__(self):
        self.current_working_directory = Path.cwd()

    def base_to_absolute_path(self, base_path):
        if base_path is None:
            absolute_base_path = self.current_working_directory
        elif base_path[0] == '/' or base_path[0] == '\\' or ( len(base_path) > 1 and base_path[1] == ':'):
            absolute_base_path = Path(base_path)
            if not absolute_base_path.is_absolute():
                # assume same drive letter (if any) as current_working_directory
                # if this box is not Windows, Path.drive returns ''
                absolute_base_path = Path(self.current_working_directory.drive + base_path)
        else:
            # assume path relative to current working directory
            absolute_base_path = self.current_working_directory / base_path
                
        # remove '/../' and parent dir with resolve()
        return absolute_base_path.resolve()
    
    def file_filter(self, relative_path):
        return False

    def file_system_search(self, base_path):
        path = self.base_to_absolute_path(base_path)
        for p in path.glob('**/*'):
            if not p.is_file():
                # for things that are not files:
                # verbose print the type of thing it is (str(type(p).__name__)) followed by the path
                continue

            if self.file_filter(p.name):
                continue

            record = {
                'hostname': socket.gethostname(),
                'file_name': p.name,
                'relative_path': p.relative_to(path),
                'full_path': path / p,
                'size': int(p.stat().st_size),
                'dropbox_hash': dropbox_hash(p),
                'created': convert_datetime_to_utc(datetime.fromtimestamp(p.stat().st_ctime)),
                'modified': convert_datetime_to_utc(datetime.fromtimestamp(p.stat().st_mtime)),
                'suffix': p.suffix,
                'mime_type': None,
                'mime_encoding': None,
            }
            record['mime_type'], record['mime_encoding'] = mimetypes.guess_type(p, strict=False)
            self.output(record)


    def output(self, record):
        print('\n', record, '\n')


crawler = Crawler()

crawler.file_system_search('..')