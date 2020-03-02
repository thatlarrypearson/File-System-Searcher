# FileSystemSearcher.py
import os
import sys
import pytz
import mimetypes
import socket
import json
import csv
import zipfile
from pathlib import Path, WindowsPath, PurePath
from platform import uname
from argparse import ArgumentParser
from datetime import datetime
from hashlib import sha256


HASH_BLOCK_SIZE = 4 * 1024 * 1024
IMAGE_SUFFIXES = (
    '.cr2', '.dng', '.gif', '.jpg', '.jpeg', '.tif', '.tiff', '.sqlite', '.sqlite3',
    '.zip',
)

def dropbox_hash(path):
    hash_list = []

    try:
        # no buffering - otherwise read fails on large files - HASH_BLOCK_SIZE > default buffer size
        with open(path, 'rb', 0) as f:
            while True:
                chunk = f.read(HASH_BLOCK_SIZE)
                if len(chunk) == 0:
                    break

                hash_list.append(sha256(chunk).digest())

    except OSError as e:

        print("\nOSError: {0}".format(e), file=sys.stderr)
        print("File Name: {0}".format(path), file=sys.stderr)
        print("Hash List Length: {0}\n".format(len(hash_list)), file=sys.stderr)
        return ''
    
    hash = sha256(b"".join(hash_list))
    return  hash.hexdigest()


def zip_dropbox_hash(z_file, zip_name, name):
    hash_list = []

    try:
        with z_file.open(name, 'r') as f:
            while True:
                chunk = f.read(HASH_BLOCK_SIZE)
                if len(chunk) == 0:
                    break

                hash_list.append(sha256(chunk).digest())

    except (OSError, zipfile.BadZipFile) as e:

        print("\nOSError: {0}".format(e), file=sys.stderr)
        print("Zip Archive File Name: {0}".format(zip_name), file=sys.stderr)
        print("File Name: {0}".format(name), file=sys.stderr)
        print("Hash List Length: {0}\n".format(len(hash_list)), file=sys.stderr)
        return ''
 
    hash = sha256(b"".join(hash_list))
    return  hash.hexdigest()


def convert_datetime_to_utc(dt):
    return pytz.utc.localize(dt)


class Publish():
    def __init__(self, output_format, output_fd):
        self.fd = output_fd
        self.record_count = 0
        self.header = None
        self.body = None
        self.footer = None

        if output_format == 'txt':
            self.header = self.txt_header
            self.body = self.txt_body
            self.footer = self.txt_footer
        elif output_format == 'json':
            self.header = self.json_header
            self.body = self.json_body
            self.footer = self.json_footer
        elif output_format == 'csv':
            self.header = self.csv_header
            self.body = self.csv_body
            self.footer = self.csv_footer
        else:
            raise ValueError("Not a valid output format: %s" % (output_format, ))
    
    def txt_header(self, record):
        first_key = True
        s = ''
        k_list = list(record)
        k_list.sort()
        for k in k_list:
            if not first_key:
                s = s + "\t"
            else:
                first_key = False
            s = s + k
        print(s, file=self.fd)
        self.txt_body(record)
    
    def txt_body(self, record):
        first_key = True
        s = ''
        k_list = list(record)
        k_list.sort()
        for k in k_list:
            if not first_key:
                s = s + "\t"
            else:
                first_key = False
            s = s + str(record[k])
        print(s, file=self.fd)
        self.record_count = self.record_count + 1

    def txt_footer(self):
        print("Records: %d" % (self.record_count, ), file=self.fd)

    def json_header(self, record):
        print('[', file=self.fd)
        self.json_body(record)

    def json_body(self, record):
        print(json.dumps(record, sort_keys=True) + ',', file=self.fd)
        self.record_count = self.record_count + 1

    def json_footer(self):
        print(']', file=self.fd)

    def csv_header(self, record):
        k_list = list(record)
        k_list.sort()
        self.csvwriter = csv.writer(self.fd, dialect='excel', delimiter='|')
        self.csvwriter.writerow(k_list)
        self.csv_body(record)

    def csv_body(self, record):
        k_list = list(record)
        k_list.sort()
        r_list = []
        for k in k_list:
            r_list.append(record[k])
        self.csvwriter.writerow(r_list)

    def csv_footer(self):
        pass

    def close(self):
        self.fd.close()


class Crawler():
    def __init__(self, volume=None, verbose=False, zip_file=False, pictures=False):
        self.current_working_directory = Path.cwd()
        self.volume = volume
        self.verbose = verbose
        self.hostname = socket.gethostname()
        self.base_path = None
        self.zip_file = zip_file
        self.pictures = pictures

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

    def file_filter(self, suffix):
        if self.pictures and not suffix.lower() in IMAGE_SUFFIXES:
            return True

        return False

    def path_crawler(self, base_path):
        self.base_path = self.base_to_absolute_path(base_path)
        return self

    def __iter__(self):
        self.path_iterator = self.base_path.glob('**/*')
        self.path_iterator.__init__()
        return self

    def __next__(self):
        p = None
        failures = 0
        while not p or not p.is_file() or self.file_filter(p.suffix):
            # for things that are not files:
            # verbose print the type of thing it is (str(type(p).__name__)) followed by the path
            try:
                p = self.path_iterator.__next__()
                failures = 0
            except (OSError, FileNotFoundError) as e:
                failures = failures + 1
                if self.verbose:
                    print("\nException: {0}".format(e), file=sys.stderr)
                    print(
                        "Crawler.__next__() {0} iterator failures on base_path: {1}\n".format(failures, self.base_path), file=sys.stderr
                    )
                if failures > 100:
                    raise StopIteration()

        record = {
            'hostname': self.hostname,
            'volume': self.volume,
            'file_name': p.name,
            'relative_path': str(p.relative_to(self.base_path)),
            'full_path': str(self.base_path / p),
            'size': int(p.stat().st_size),
            'dropbox_hash': dropbox_hash(p),
            'created': (convert_datetime_to_utc(datetime.fromtimestamp(p.stat().st_ctime))).isoformat(),
            'modified': (convert_datetime_to_utc(datetime.fromtimestamp(p.stat().st_mtime))).isoformat(),
            'suffix': p.suffix,
            'mime_type': None,
            'mime_encoding': None,
        }

        record['mime_type'], record['mime_encoding'] = mimetypes.guess_type(p, strict=False)

        return record

    def file_system_search(self, base_path):
        for record in self.path_crawler(base_path):
            self.output(record)

    def output(self, record):
        print(record)


class ZipCrawler():

    def __init__(self, zipfile, volume, verbose=False, pictures=False):
        self.file = zipfile
        self.current_working_directory = Path.cwd()
        self.volume = volume
        self.verbose = verbose
        self.hostname = socket.gethostname()
        self.base_path = zipfile
        self.stop_iterator = False
        self.pictures = pictures

    def file_filter(self, suffix):
        if self.pictures and not suffix.lower() in IMAGE_SUFFIXES:
            return True

        return False

    def __iter__(self):
        try:
            self.z_file = zipfile.ZipFile(self.base_path)
            self.z_name_iter = iter(self.z_file.namelist())

        except (OSError, zipfile.BadZipFile) as e:
            # Zip file is damaged and/or otherwise unreadable.
            self.stop_iterator = True
            if self.verbose:
                print("\nzipfile.BadZipFile: {0}".format(e), file=sys.stderr)
                print("ZipCrawler.__iter__(): Exception: BadZipFile: {0}\n".format(self.base_path), file=sys.stderr)

        return self
    
    def __next__(self):
        if self.stop_iterator:
            raise StopIteration()
        try:
            name = self.z_name_iter.__next__()
            info = self.z_file.getinfo(name)

            # skip directories
            # this is where you might also add filtering capabilities
            while info.is_dir():
                name = self.z_name_iter.__next__()
                info = self.z_file.getinfo(name)

            p = Path(name)
            while self.pictures and not self.file_filter(p.suffix):
                name = self.z_name_iter.__next__()
                info = self.z_file.getinfo(name)
                p = Path(name)


            utc_dt = (convert_datetime_to_utc(datetime(
                    info.date_time[0],
                    info.date_time[1],
                    info.date_time[2],
                    hour=info.date_time[3],
                    minute=info.date_time[4],
                    second=info.date_time[5]
                ))).isoformat()

            full_path = self.file + os.path.sep + name
            if os.path.sep == "\\":
                full_path = full_path.replace('/', "\\")
            record = {
                    'hostname': self.hostname,
                    'volume': self.volume,
                    'file_name': info.filename,
                    'relative_path': name,
                    'full_path': full_path,
                    'size': info.file_size,
                    'dropbox_hash': zip_dropbox_hash(self.z_file, self.file, name),
                    'created': utc_dt,
                    'modified': utc_dt,
                    'suffix': p.suffix,
                    'mime_type': None,
                    'mime_encoding': None,
                }

            record['mime_type'], record['mime_encoding'] = mimetypes.guess_type(p, strict=False)

        except (OSError, zipfile.BadZipFile) as e:
            if self.verbose:
                print("\nzipfile.BadZipFile: {0}".format(e), file=sys.stderr)
                print("ZipCrawler.__next__(): Exception: BadZipFile: {0}\n".format(self.base_path), file=sys.stderr)
            raise StopIteration()

        return record


def main_loop(args, publish):
    crawler = Crawler(volume=args['volume'], verbose=args['verbose'])

    first_time = True
    for base_path in args['base_paths']:
        for record in crawler.path_crawler(base_path):
            if first_time:
                first_time = False
                publish.header(record)
            else:
                publish.body(record)

            if args['search_zip_files'] and record['suffix'] in ['.zip', ]:
                zcrawler = ZipCrawler(record['full_path'], volume=args['volume'], verbose=args['verbose'])

                for record in zcrawler:
                    publish.body(record)

    publish.footer()


def main():
    parser = ArgumentParser(
            description="File System Searcher - Search for files and output records with useful info."
        )
    parser.add_argument(
            "base_paths",
            nargs='*',
            metavar="base_path",
            default=[".", ],
            help="Relative or absolute directory path where the file search begins. Default: current working directory."
        )
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", action="store_true")
    parser.add_argument("--output_file", help="Output file name.", default=sys.stdout)
    parser.add_argument(
            "--volume", 
            help="""Output the user provided volume name with all output records.
            Used to help users associate external USB drives with records.""",
            default=None
        )
    parser.add_argument(
            "--output_format",
            help="Output format",
            choices=["txt", "csv", "json", ],
            default="txt"
        )
    parser.add_argument(
            "--search_zip_files",
            help="Include files found in zip files in results.",
            default=False,
            action='store_true'
        )
    args = vars(parser.parse_args())

    if isinstance(args['output_file'], str):
        if args['output_format'] == 'csv':
            output_fd = open(args['output_file'], mode='w', newline='')
        else:
            output_fd = open(args['output_file'], mode='w')
    else:
        output_fd = args['output_file']

    publish = Publish(args['output_format'], output_fd)

    main_loop(args, publish)

    publish.close()

if __name__ == "__main__":
    # execute only if run as a script
    main()