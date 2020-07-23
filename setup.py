from setuptools import setup, find_packages
setup(
    name="file-system-searcher",
    version="0.3",
    py_modules=['file_system_searcher', ],
    python_requires='>=3.6',
    install_requires=['pytz',],

    author="Larry Pearson",
    author_email="DoNotReply@gmail.com",
    license='MIT',
    description="Library and script to search directories (including archives) to collect and output file metadata.",
    long_description_content_type="text/markdown",
    long_description=open('README.md').read(),
    keywords=[
        'find', 'directory', 'file', 'zip', 'tar', 'hash',
    ],
    url="https://github.com/thatlarrypearson/File-System-Searcher",   # project home page, if any
    project_urls={
        "Bug Tracker": "https://github.com/thatlarrypearson/File-System-Searcher",
        "Documentation": "https://github.com/thatlarrypearson/File-System-Searcher",
        "Source Code": "https://github.com/thatlarrypearson/File-System-Searcher",
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Programming Langauge :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
