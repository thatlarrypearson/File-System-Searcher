# File System Searcher

Searches for files starting at the given path and outputs records with a variety of useful fields.

## Usage

FileSystemSearcher \[options\] \[base_path1 \[base_path2\] ... \]

### \[options\]
* ```--volume=name```
  Output the user provided ```volume``` name with all output records.  Default is None.  Used to help users associate external USB drives with records.
* ```--output-file-format=off```
  Output file format or 'off' can be one of ```text```,  ```CSV``` or ```JSON```.
  * ```text```
    Simplistic report format
  * ```CSV```
    Comma seperated values that can be imported by Microsoft Excel.  See the Python [csv](https://docs.python.org/3/library/csv.html) library.
  * ```JSON```
    The output is put into a ```list()``` of records composed of dictionaries - ```dict()```.  The output is then converted into JSON format.
* ```base_path```
  The relative or absolute path to the directory where the file search should begin.  When not present, the ```base_path``` defaults to the current working directory.

## Output Fields

* hostname
  The computer's name on the network.
* volume
  User provided volume name associated with all files in the output set.
* file_name
  The file name indipeneent of where it sits within the file system.
* relative_path
  The directory path from the base path to the directory the file sits in.
* base_path
  The "base path" is the full path to the directory where the search for files started.
* size
  File size in bytes.
* dropbox_hash
  A hash of hashes made using the same method that Dropbox uses in their public API's.
* created
  File creation timestamp or None if not available.
* modified
  File last modified timestamp or None if not available.
* suffix
  File suffix.  E.g. file name '```picture.jpg```' suffix is '```jpg```'.
* mime_type
  MIME type as determined by [Python ```mimetypes```](https://docs.python.org/3/library/mimetypes.html)

## File Formats

* CSV

* JSON

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

## Requierd Python Libraries

The following Python Libraries are required for installation.

* [```python-magic```](https://github.com/ahupp/python-magic)

