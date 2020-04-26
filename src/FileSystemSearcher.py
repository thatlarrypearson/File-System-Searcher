# FileSystemSearcher.py
import os
import sys
import pytz
import mimetypes
import socket
import json
import csv
import zipfile
import tarfile
from pathlib import Path, WindowsPath, PurePath
from platform import uname
from argparse import ArgumentParser
from datetime import datetime, MINYEAR
from hashlib import sha256

# try:
#     import fcntl
#     def local_fcntl(fd):
#         orig_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
#         fcntl.fcntl(fd, fcntl.F_SETFL, orig_flags | os.O_NONBLOCK)

# except ImportError:
#     def local_fcntl(fd):
#         pass

HASH_BLOCK_SIZE = 4 * 1024 * 1024


def dropbox_hash(path, verbose=False):
    hash_list = []

    try:
        # no buffering - otherwise read fails on large files - HASH_BLOCK_SIZE > default buffer size
        with open(path, 'rb', 0) as fd:
            # local_fcntl(fd)
            while True:
                chunk = fd.read(HASH_BLOCK_SIZE)
                if not chunk or len(chunk) == 0:
                    break

                hash_list.append(sha256(chunk).digest())

    except:
        if verbose:
            e = sys.exc_info()[0]
            print("\nException: {0}".format(e), file=sys.stderr)
            print("File Name: {0}".format(path), file=sys.stderr)
            print("Hash List Length: {0}\n".format(len(hash_list)), file=sys.stderr)
        return ''
    
    hash = sha256(b"".join(hash_list))
    return  hash.hexdigest()


def zip_dropbox_hash(z_file, zip_name, name, verbose=False):
    hash_list = []

    try:
        with z_file.open(name, 'r') as f:
            while True:
                chunk = f.read(HASH_BLOCK_SIZE)
                if len(chunk) == 0:
                    break

                hash_list.append(sha256(chunk).digest())

    except:
        if verbose:
            e = sys.exc_info()[0]
            print("\nException: {0}".format(e), file=sys.stderr)
            print("Zip Archive File Name: {0}".format(zip_name), file=sys.stderr)
            print("File Name: {0}".format(name), file=sys.stderr)
            print("Hash List Length: {0}\n".format(len(hash_list)), file=sys.stderr)
        return ''
 
    hash = sha256(b"".join(hash_list))
    return  hash.hexdigest()

def tar_dropbox_hash(tar, tarinfo, tar_file_name, file_name, verbose=False):
    hash_list = []

    try:
        fd = tar.extractfile(tarinfo)
        while True:
            chunk = fd.fread(HASH_BLOCK_SIZE)
            if len(chunk) == 0:
                break

            hash_list.append(sha256(chunk).digest())

    except:
        if verbose:
            e = sys.exc_info()[0]
            print("\nException: {0}".format(e), file=sys.stderr)
            print("Tar Archive File Name: {0}".format(tar_file_name), file=sys.stderr)
            print("File Name: {0}".format(file_name), file=sys.stderr)
            print("Hash List Length: {0}\n".format(len(hash_list)), file=sys.stderr)
        return ''
 
    hash = sha256(b"".join(hash_list))
    return  hash.hexdigest()

def convert_datetime_to_utc(dt):
    return pytz.utc.localize(dt)

ZIP_FILE_SUFFIXES = [
    '.zip', '.7z',
]

def is_zip_file(file_name):
    for suffix in ZIP_FILE_SUFFIXES:
        if file_name.lower().endswith(suffix):
            return True
    return False

TAR_FILE_SUFFIXES = [
    '.tar', '.tgz', '.tar.bz2', 'tar.gz',
]

def is_tar_file(file_name):
    for suffix in TAR_FILE_SUFFIXES:
        if file_name.lower().endswith(suffix):
            return True
    return False


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
    def __init__(self, volume=None, verbose=False, search_archives=False, hash=True):
        self.current_working_directory = Path.cwd()
        self.volume = volume
        self.verbose = verbose
        self.hostname = socket.gethostname()
        self.base_path = None
        self.hash = hash
        self.mode = 'Crawler'
        self.zip_crawler = None
        self.tar_crawler = None
        self.archive_name = None
        self.search_archives = search_archives

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

    def path_crawler(self, base_path):
        self.base_path = self.base_to_absolute_path(base_path)
        return self

    def __iter__(self):
        self.path_iterator = self.base_path.glob('**/*')
        self.path_iterator.__init__()
        return self
    
    def __next__(self):
        if self.mode == 'Crawler':
            record = self.next_crawler()
            if self.search_archives and is_tar_file(record['file_name']):
                self.mode = 'TarCrawler'
            elif self.search_archives and is_zip_file(record['file_name']):
                self.mode = 'ZipCrawler'
            return record
        elif self.mode == 'TarCrawler':
            if not self.tar_crawler:
                self.tar_crawler = TarCrawler(
                    record['full_path'], volume=self.volume, verbose=self.verbose, hash=self.hash
                )
                self.tar_crawler = self.tar_crawler.__iter__()
            try:
                record = self.tar_crawler.__next__()
                if record is None:
                    raise StopIteration()
                return record
            except StopIteration:
                self.mode = 'Crawler'
                self.tar_crawler = None
                return self.__next__()
        elif self.mode == 'ZipCrawler':
            if not self.zip_crawler:
                self.zip_crawler = ZipCrawler(
                    record['full_path'], volume=self.volume, verbose=self.verbose, hash=self.hash
                )
                self.zip_crawler = self.zip_crawler.__iter__()
            try:
                record = self.zip_crawler.__next__()
                if record is None:
                    raise StopIteration()
                return record
            except StopIteration:
                self.mode = 'Crawler'
                self.zip_crawler = None
                return self.__next__()
        raise StopIteration()

    def next_crawler(self):
        p = None
        failures = 0
        is_file = False
        while not p or not is_file:
            # for things that are not files:
            # verbose print the type of thing it is (str(type(p).__name__)) followed by the path
            if p:
                try:
                    is_file = p.is_file()
                except PermissionError as e:
                    is_file = False
                    if self.verbose:
                        print("\nException: {0}".format(e), file=sys.stderr)
                        print("Crawler.__next__(): pathlib Path.is_file() failure on base_path: {0}\n".format(self.base_path),
                            file=sys.stderr)
            if p and is_file:
                break
            try:
                p = self.path_iterator.__next__()
                failures = 0
            except (OSError, FileNotFoundError) as e:
                failures = failures + 1
                if self.verbose:
                    print("\nException: {0}".format(e), file=sys.stderr)
                    print(
                        "Crawler.__next__() {0} iterator failures on base_path: {1}\n".format(failures, self.base_path),
                        file=sys.stderr)
                if failures > 10:
                    # This might be overkill.
                    # Generally when these exceptions occur, the iterator is done and won't restart on the first try.
                    raise StopIteration()

        created = (convert_datetime_to_utc(datetime.fromtimestamp(p.stat().st_ctime))).isoformat()
        modified = (convert_datetime_to_utc(datetime.fromtimestamp(p.stat().st_mtime))).isoformat()

        record = {
            'hostname': self.hostname,
            'volume': self.volume,
            'file_name': self.get_file_name(p),
            'relative_path': str(p.relative_to(self.base_path)),
            'full_path': str(self.base_path / p),
            'size': int(p.stat().st_size),
            'dropbox_hash': '',
            'created': created,
            'modified': modified,
            'suffix': p.suffix,
            'mime_type': None,
            'mime_encoding': None,
            'is_archive': False,
        }

        record['mime_type'], record['mime_encoding'] = mimetypes.guess_type(p, strict=False)

        if self.hash and record['size'] > 0:
            if self.verbose:
                print("%s, %d" % (str(p), record['size'], ), file=sys.stderr)
            record['dropbox_hash'] = dropbox_hash(p, verbose=self.verbose)
        
        if (not created or not modified) and self.verbose:
            print('\ncreated or modified is None\n', record, '\n', file=sys.stderr)

        return record
    
    def get_file_name(self, name):
        name = str(name)
        if '/' in name:
            parts = name.split('/')
            return parts[-1]
        elif '\\' in name:
            parts = name.split('\\')
            return parts[-1]
        return name

    def file_system_search(self, base_path):
        for record in self.path_crawler(base_path):
            self.output(record)

    def output(self, record):
        print(record)


class ZipCrawler():
    def __init__(self, zipfile, volume, verbose=False, hash=True):
        self.file = zipfile
        self.current_working_directory = Path.cwd()
        self.volume = volume
        self.verbose = verbose
        self.hostname = socket.gethostname()
        self.base_path = zipfile
        self.stop_iterator = False
        self.hash = hash

    def __iter__(self):
        try:
            self.z_file = zipfile.ZipFile(self.base_path)
            self.z_name_iter = iter(self.z_file.namelist())

        except:
            # Zip file may be damaged and/or otherwise unreadable.
            self.stop_iterator = True
            if self.verbose:
                e = sys.exc_info()[0]
                print("\nException: {0}".format(e), file=sys.stderr)
                print("Tar Archive File: {0}\n".format(self.base_path), file=sys.stderr)

        return self
    
    def __next__(self):
        if self.stop_iterator:
            raise StopIteration()
        try:
            # name is really a path within the archive
            name = self.z_name_iter.__next__()
            info = self.z_file.getinfo(name)

            # skip directories
            while info.is_dir():
                name = self.z_name_iter.__next__()
                info = self.z_file.getinfo(name)
            
            file_name = self.get_file_name(name)

            try:
                utc_dt = (convert_datetime_to_utc(datetime(
                        info.date_time[0],
                        info.date_time[1],
                        info.date_time[2],
                        hour=info.date_time[3],
                        minute=info.date_time[4],
                        second=info.date_time[5]
                    ))).isoformat()
            except ValueError as e:
                # some zip file date records have out-of-bound values
                # this value should show up as 0001-01-01
                utc_dt = (convert_datetime_to_utc(datetime(MINYEAR, 1, 1))).isoformat()

            full_path = self.file + os.path.sep + name
            if os.path.sep == "\\":
                full_path = full_path.replace('/', "\\")
            record = {
                    'hostname': self.hostname,
                    'volume': self.volume,
                    'file_name': file_name,
                    'relative_path': name,
                    'full_path': full_path,
                    'size': info.file_size,
                    'dropbox_hash': '',
                    'created': utc_dt,
                    'modified': utc_dt,
                    'suffix': self.get_suffix(file_name),
                    'mime_type': None,
                    'mime_encoding': None,
                    'is_archive': True,
                }

            record['mime_type'], record['mime_encoding'] = mimetypes.guess_type(file_name, strict=False)

            if hash and record['size'] > 0:
                record['dropbox_hash'] = zip_dropbox_hash(self.z_file, self.file, name)

        except (OSError, zipfile.BadZipFile) as e:
            if self.verbose:
                print("\nzipfile.BadZipFile: {0}".format(e), file=sys.stderr)
                print("ZipCrawler.__next__(): Exception: BadZipFile: {0}\n".format(self.base_path), file=sys.stderr)
            raise StopIteration()

        return record

    def get_suffix(self, file_name):
        if "." not in file_name:
            return None
        parts = file_name.split('.')
        if len(parts[-1]) > 15:
            return None
        return parts[-1]

    def get_file_name(self, name):
        name = str(name)
        if "/" not in name:
            return name
        parts = name.split('.')
        return parts[-1]

class TarCrawler():
    def __init__(self, tar_file_path, volume, verbose=False, hash=True):
        self.file = tar_file_path
        self.current_working_directory = Path.cwd()
        self.volume = volume
        self.verbose = verbose
        self.hostname = socket.gethostname()
        self.base_path = tar_file_path
        self.stop_iterator = False
        self.hash = hash

    def __iter__(self):
        try:
            # open archive and prepare to iterate
            self.tar = tarfile.open(self.base_path)
            self.tar_iter = iter(self.tar)

        except:
            # Zip file is damaged and/or otherwise unreadable.
            self.stop_iterator = True
            if self.verbose:
                e = sys.exc_info()[0]
                print("\nException: {0}".format(e), file=sys.stderr)
                print("Tar Archive File Name: {0}".format(self.file), file=sys.stderr)

        return self
    
    def __next__(self):
        if self.stop_iterator:
            raise StopIteration()
        try:
            # name is really a path within the archive
            tarinfo = self.tar_iter.__next__()

            # skip directories
            while not tarinfo.isfile():
                tarinfo = self.tar_iter.__next__()
            
            file_name = self.get_file_name(tarinfo.name)

            try:
                utc_dt = (convert_datetime_to_utc(datetime.fromtimestamp(tarinfo.mtime))).isoformat()
            except ValueError as e:
                # some tar file date records may have out-of-bound values
                # these should show up as 0001-01-01
                utc_dt = (convert_datetime_to_utc(datetime(MINYEAR, 1, 1))).isoformat()
            except:
                e = sys.exc_info()[0]
                print("\nException: {0}".format(e), file=sys.stderr)
                print("Tar Archive File Name: {0}".format(self.file), file=sys.stderr)
                print("tarinfo.mtime:", tarinfo.mtime, file=sys.stderr)
               

            full_path = self.file + os.path.sep + file_name
            if os.path.sep == "\\":
                full_path = full_path.replace('/', "\\")
            record = {
                    'hostname': self.hostname,
                    'volume': self.volume,
                    'file_name': file_name,
                    'relative_path': file_name,
                    'full_path': full_path,
                    'size': tarinfo.size,
                    'dropbox_hash': '',
                    'created': utc_dt,
                    'modified': utc_dt,
                    'suffix': self.get_suffix(file_name),
                    'mime_type': None,
                    'mime_encoding': None,
                    'is_archive': True,
                }

            record['mime_type'], record['mime_encoding'] = mimetypes.guess_type(file_name, strict=False)

            if hash and record['size'] > 0:
                record['dropbox_hash'] = tar_dropbox_hash(self.tar, tarinfo, self.file, tarinfo.name, verbose=self.verbose)

        except (OSError, zipfile.BadZipFile) as e:
            if self.verbose:
                print("\nzipfile.BadZipFile: {0}".format(e), file=sys.stderr)
                print("ZipCrawler.__next__(): Exception: BadZipFile: {0}\n".format(self.base_path), file=sys.stderr)
            raise StopIteration()

        return record

    def get_suffix(self, file_name):
        if "." not in file_name:
            return None
        parts = file_name.split('.')
        if len(parts[-1]) > 15:
            return None
        return parts[-1]

    def get_file_name(self, name):
        name = str(name)
        if "/" not in name:
            return name
        parts = name.split('.')
        return parts[-1]


def main_loop(args, publish):
    crawler = Crawler(volume=args['volume'], verbose=args['verbose'], hash=(not args['no_hash']))

    first_time = True
    for base_path in args['base_paths']:
        for record in crawler.path_crawler(base_path):
            if first_time:
                first_time = False
                publish.header(record)
            else:
                publish.body(record)

            # if args['search_archives'] and is_tar_file(record['file_name']):
            #     tcrawler = TarCrawler(
            #         record['full_path'], volume=args['volume'], verbose=args['verbose'], hash=(not args['no_hash']))
            #     for record in tcrawler:
            #         publish.body(record)
            # if args['search_archives'] and is_zip_file(record['file_name']):
            #     zcrawler = ZipCrawler(
            #         record['full_path'], volume=args['volume'], verbose=args['verbose'], hash=(not args['no_hash']))
            #     for record in zcrawler:
            #         publish.body(record)

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
            default="json"
        )
    parser.add_argument(
            "--search_archives",
            help="Include files found in archives (zip, tar) in results.",
            default=False,
            action='store_true'
        )
    parser.add_argument(
            "--no_hash",
            help="Turn of dropbox_hash generation.",
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