# https://docs.djangoproject.com/en/3.0/howto/custom-management-commands/
from time import sleep
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import DataError, OperationalError
from FileSystemSearcher.FileSystemSearcher import Crawler, ZipCrawler
from FileSystemSearcher.models import FileInfo
from FileSystemSearcher.forms import FileInfoForm


class Command(BaseCommand):
    help = 'Searches a file system and loads file information into the database'

    def add_arguments(self, parser):
        parser.add_argument(
                "base_paths",
                nargs='*',
                metavar="base_path",
                default=[".", ],
                help="Relative or absolute directory path where the file search begins. Default: current working directory."
            )
        parser.add_argument(
                "--volume", 
                help="""Output the user provided volume name with all output records.
                Used to help users associate external USB drives with records.""",
                default=None
            )
        parser.add_argument(
                "--search_archives",
                help="Include files found in zip files in results.",
                default=False,
                action='store_true'
            )
        parser.add_argument(
            "--no_hash",
            help="Do NOT generate Dropbox type hashes of files.",
            default=False,
            action='store_true'
        )


    def handle(self, *args, **options):
        # volume=None, verbose=False, search_archives=False, hash=True
        crawler = Crawler(
                volume=options['volume'], 
                verbose=options['verbosity'],
                search_archives=options['search_archives'],
                hash=(not options['no_hash'])
                
            )

        for base_path in options['base_paths']:
            for record in crawler.path_crawler(base_path):
                for k, v in record.items():
                    if v is None:
                        record[k] = ''

                form = FileInfoForm(record)

                if form.is_valid():
                    file_info = form.save(commit=False)
                    file_info.created = record['created']
                    file_info.modified = record['modified']

                    try:
                        file_info.save()
                    except (OperationalError, DataError) as e:
                        print('\n', e, '\n', record, '\n')
                else:
                    print('\n', form.errors, '\n', record, '\n')

                # if options['search_zip_files'] and record['suffix'] in ['.zip', ]:
                #     zcrawler = ZipCrawler(
                #             record['full_path'], 
                #             volume=options['volume'], 
                #             verbose=options['verbosity']
                #         )

                #     for record in zcrawler:
                #         for k, v in record.items():
                #             if v is None:
                #                 record[k] = ''

                #         form = FileInfoForm(record)
                        
                #         if form.is_valid():
                #             file_info = form.save(commit=False)
                #             file_info.created = record['created']
                #             file_info.modified = record['modified']

                #             try:
                #                 file_info.save()
                #             except (OperationalError, DataError) as e:
                #                 print('\n', e, '\n', record, '\n')
                #         else:
                #             print('\n', form.errors, '\n', record, '\n')

    


