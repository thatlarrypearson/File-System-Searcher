# FileSystemSearcher.py
import os
import sys
import pytz
import mimetypes
import socket
import json
import csv
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
        self.csvwriter = csv.writer(self.fd)
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


# https://docs.python.org/3/library/pathlib.html
# https://docs.python.org/3/library/mimetypes.html
# https://docs.python.org/3/library/csv.html
# https://sahandsaba.com/interview-question-iterator-of-iterators-and-cantor-set-theory.html


class Crawler():
    def __init__(self, volume=None, verbose=False):
        self.current_working_directory = Path.cwd()
        self.volume = volume
        self.verbose = verbose
        self.hostname = socket.gethostname()
        self.base_path = None

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

    def path_crawler(self, base_path):
        self.base_path = self.base_to_absolute_path(base_path)
        return self

    def __iter__(self):
        self.path_iterator = self.base_path.glob('**/*')
        self.path_iterator.__init__()
        return self

    def __next__(self):
        p = self.path_iterator.__next__()   
        while not p.is_file() or self.file_filter(p.name):
            # for things that are not files:
            # verbose print the type of thing it is (str(type(p).__name__)) followed by the path
            p = self.path_iterator.__next__()

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


# https://docs.python.org/3/howto/argparse.html
# https://docs.python.org/3/library/argparse.html#module-argparse
# https://docs.python.org/3/library/argparse.html


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
    args = vars(parser.parse_args())

    if isinstance(args['output_file'], str):
        if args['output_format'] == 'csv':
            output_fd = open(args['output_file'], mode='w', newline='')
        else:
            output_fd = open(args['output_file'], mode='w')
    else:
        output_fd = args['output_file']

    crawler = Crawler(volume=args['volume'], verbose=args['verbose'])
    
    publish = Publish(args['output_format'], output_fd)

    first_time = True
    for base_path in args['base_paths']:
        for record in crawler.path_crawler(base_path):
            if first_time:
                first_time = False
                publish.header(record)
            else:
                publish.body(record)
        publish.footer()

if __name__ == "__main__":
    # execute only if run as a script
    main()