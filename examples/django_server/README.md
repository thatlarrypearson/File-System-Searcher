# FileSystemSearcher Django Server

This code is useful for people who might want to place their file system information into a database.

Making this code work requires some Django web framework skills.

## Instructions

- Change directory to ```examples/django_server

- Edit ```server/settings.py``` to configure the database settings.

- Copy ```FileSystemSearcher.py``` from ```../../src/``` to ```FileSystemSearcher/```

- Run ```python3.8 manage.py makemigrations FileSystemSearcher```

- Run ```python3.8 manage.py migrate```

- Run ```python 3.8 manage.py migrate createsuperuser```

- Understand the arguements to ```get_file_system``` by running the following.

```powershell
> python3.8 manage.py get_file_system --help
usage: manage.py get_file_system [-h] [--volume VOLUME] [--search_archives] [--no_hash] [--version] [-v {0,1,2,3}]
                                 [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                                 [--force-color] [--skip-checks]
                                 [base_path [base_path ...]]

Searches a file system and loads file information into the database

positional arguments:
  base_path             Relative or absolute directory path where the file search begins. Default: current working
                        directory.

optional arguments:
  -h, --help            show this help message and exit
  --volume VOLUME       Output the user provided volume name with all output records. Used to help users associate
                        external USB drives with records.
  --search_archives     Include files found in zip files in results.
  --no_hash             Do NOT generate Dropbox type hashes of files.
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided,
                        the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
  --skip-checks         Skip system checks.
>
```

Then to run this on my Windows 10 machine and just get my pictures from my ```Pictures``` directory:

```powershell
> python3.8 manage.py get_file_system --volume widebody_d --search_archives --pictures D:\runar\Pictures\
```

It works the same way with Linux and Mac.
