# File System Searcher

Search for files starting at the given path and output records with useful information.  Can be used as a command line program or as an iterable class in a ```for``` loop in a Python program.

## Script Usage

```text
python3.8 -m file_system_searcher.py \[options\] \[base_path1 \[base_path2\] ... \]
```

### \[options\]

* ```--volume=name```

  Output the user provided ```volume``` name with all output records.  Default is None.  Used to help users associate external USB drives with records.

* ```--output_file=name```

  Output file name.  Defaults to standard output (stdout).

* ```--output_format=format```

  Output format or can be one of ```text```,  ```csv``` or ```json```.

  * ```text```

    Simplistic report format.

  * ```csv```

    ```|``` seperated values that can be imported by Microsoft Excel and Access.  See the Python [CSV](https://docs.python.org/3/library/csv.html) library.

  * ```json```

    JSON format means that each individual record is encoded in JSON format and each record is terminated by ```<CR><LF>``` on Windows or ```<LF>``` on Unix/Linux and variants.

* ```--search_archives```

  Include files found in zip (```'.zip'```) and tar (```'.tar'```, ```'.tgz'```, ```'.tar.bz2'``` and ```'tar.gz'```) archives in results.  Otherwise, archive files will only be noted.  When enabled, ```relative_path``` is relative to the zip archive.  ```full_path``` treats the zip archive file as a directory in the path to the archived file.

* ```--no_hash```

  Do not generate ```dropbox_hash``` values in the output records.  Default is to generate ```dropbox_hash``` values.  Using this option will significantly speed up file system searches.

### Base Paths

* ```base_path```
  The relative or absolute path to the directory where the file search should begin.  When not present, the ```base_path``` defaults to the current working directory.

## Output Fields

* hostname

  The computer's name on the network.

* volume

  User provided volume name associated with all files in the output set.

* file_name

  The file name without directory/folder location.

* relative_path

  The directory/folder path from the base path directory/folder to the directory/folder the file sits in.

* base_path

  The "base path" is the full path to the directory/folder where the search for files started.

* size

  File size in bytes.

* dropbox_hash

  A hash of hashes made using the same method that Dropbox uses in their public API's.  This hash is sufficient to uniquely identify files having the same contents.   Matching records based on hashes is one way to find duplicate files within a large set of files.

* created

  File creation timestamp or None if not available.

* modified

  File last modified timestamp or None if not available.

* suffix

  File suffix.  E.g. file name '```picture.jpg```' suffix is '```jpg```'.

* mime_type

  MIME type is determined by [Python ```mimetypes```](https://docs.python.org/3/library/mimetypes.html)

* mime_encoding

  MIME encoding is determined by [Python ```mimetypes```](https://docs.python.org/3/library/mimetypes.html)

* is_archive

  Used to identify records generated from an archive file's contents.  That is, ```is_archive``` is true when the file came from an archive.

## Output File Formats

* CSV

* JSON

* Text

## Required Python Versions

The software has been tested on:

* Windows 10 on 64 Bit X86

  * Python 3.8
  * Python 3.7
  * Anaconda Python 3.8
  * Anaconda Python 3.7
  * Anaconda Python 3.6

* Linux Mint on 32 and 64 Bit X86

  * Python 3.8
  * Python 3.7
  * Python 3.6

* Raspbian on 64 Bit ARM7

  * Python 3.8
  * Python 3.7
  * Python 3.6

## Required Python Libraries

The following Python libraries need to be added to support running this program:

* ```pytz```

```bash
python3.8 -m pip install pytz
```

## Installation

### Developer Mode Install

Developers who wish to modify the code can clone from ```github``` and install with pip.  This enables changes made in the code to appear immediately as though they were happening in the library.

```bash
python3.8 -m pip install pip --upgrade
python3.8 -m pip install setuptools --upgrade
python3.8 -m pip install wheel --upgrade
python3.8 -m pip install pytz --upgrade
git clone https://github.com/thatlarrypearson/File-System-Searcher.git
cd File-System-Searcher
python3.8 setup.py sdist
python3.8 -m pip install -e .
```

### Check Installation

Launch the ```python``` interpreter ```python3.8``.`

```python
from file_system_searcher import Crawler
```

An alternative to the above approach is to simply run the program as shown below.

```PowerShell
python3.8 -m file_system_searcher --help
```

No errors?  You are installed!

## Process Seems To Hang Or Go Into Infinite Loop

On Linux and Unix varients, the FileSystemSearcher process can seem to hang when searching the entire file system.  The problem occurs in the ```dropbox_hash(path, verbose=False)``` function.  This function computes a hash value of the data in the file using the same method as Dropbox uses in their APIs.  Problems occur with files that aren't the same kind of file as a persistant storage file.

When file hash values aren't needed, a flag can be set to disable the file hash feature.  However, when hash values are needed, the starting path for ```FileSystemSearcher``` should not include ```/dev``` or ```/proc``` as these paths contain device files that cause reads designed for regular files to fail.

For example, ```/dev/tty01```, typically represents a serial interface device.  In this case, reads would block if there wasn't any input on that serial device.  The program would appear to hang.  Some USB devices would also behave in this way.

Another example, ```/dev/core```, a symbolic link to ```/proc/kcore``` on some Debian based systems, is the virtual allocation of memory in the kernel. On 64 bit systems that size can be an absolute limit of 128T (140,737,477,885,952 bytes) since that is the most the system can allocate.  In theory, the ```dropbox_hash(path, verbose=False)``` function could read through this but in practice, the time it would take could be months or years depending on the processor.

## Searching Apple Mac ```Time Machine``` Backups From Linux Systems

After mounting an Apple Mac backup volume on a Linux Mint version 19.3 system, searching the entire backup volume introduced data errors on a specific volume root directory.  When limiting the search to another directory, the results were as expected.

Avoid ```.HFS+ Private Directory Data<CTRL-M>/```.  In the results, ```relative_path``` and ```full_path``` are completely wrong.

* relative_path is missing ```/<file-name>```.
* full_path is missing ```<base-path>/``` and ```/<file-name```.

The directory ```Backups.backupdb/``` in the root of the backup file system processes correctly with the expected results.  This is the directory containing the backups.

## Process Killed Without Error Message

On systems with strong security controls, access attempts on priveldged files can cause the operating system or antivirus software to kill the offending program.  One example is on Windows 10 when reading a home directory.  Windows 10 home directories contain ```NTUSER.DAT``` and similarly named files.  Attempts to read this file in the ```hash``` functions initiates a defensive response by antivirus software.  The antivirus software kills the reader - this program.

## Getting Arguments

```powershell
PS C:\Users\human\Dropbox\src\FileSystemSearcher\src> python3.8 -m file_system_searcher.py --help
usage: file_system_searcher.py [-h] [-v] [--output_file OUTPUT_FILE] [--volume VOLUME] [--output_format {txt,csv,json}]
                             [--search_archives] [--no_hash]
                             [base_path [base_path ...]]

File System Searcher - Search for files and output records with useful info.

positional arguments:
  base_path             Relative or absolute directory path where the file search begins. Default: current working
                        directory.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose mode
  --output_file OUTPUT_FILE
                        Output file name.
  --volume VOLUME       Output the user provided volume name with all output records. Used to help users associate
                        external USB drives with records.
  --output_format {txt,csv,json}
                        Output format
  --search_archives     Include files found in archives (zip, tar) in results.
  --no_hash             Turn of dropbox_hash generation.
PS C:\Users\human\Dropbox\src\FileSystemSearcher\src>
```

## Class ```Crawler(base_path=None, volume=None, verbose=False, search_archives=False, hash=True)```

Where

* ```base_path``` (required) is the full or relative path to where the search should start.

* ```volume``` defaults to None and can be any string that represents the physical hard drive or host machine the file search was conducted on.

* ```verbose```, when ```True```, will output extra information helpful in following progress and failures.

* ```search_archives```, when ```True```, will cause archive files to be searched in the same way that a file system is searched providing similar output.

* ```hash```, when ```True```, the default, causes hash values to be generated for each file in the output.

### Example Class Usage

```python
from file_system_searcher import Crawler

crawler = Crawler(base_path='.')

for record in crawler:
  print record
```
