from setuptools import setup
setup(
    name = "text-transpose",
    version = "1.0.0",
    entry_points = {
        'console_scripts': ['transpose=transpose:main'],
    },
    py_modules=['transpose'],
    author = "Willem Hengeveld",
    author_email = "itsme@xs4all.nl",
    description = "Transpose, flip, rotate textual data.",
    long_description_content_type='text/markdown',
    long_description="""
Commandline tool which can transpose, flip, rotate data formatted in rows and columns.
With many ways to define how the columns are defined. Rotations can be multiples of 45 degrees.

simple transpose: `transpose`

    a b c
    d e f

to

    a   d   
    b   e   
    c   f   


rotate by 45 degrees: `transpose -45`

    a b c
    d e f
    g h i

to

            a       
        d       b   
    g       e       c
        h       f   
            i       

or reverse a line:

    transpose -y -p .

""",

    license = "MIT",
    keywords = "transpose, row-column-data, rotate, filter",
    url = "https://github.com/nlitsme/transpose/",
    classifiers = [
        'Topic :: Text Processing :: Filters',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    python_requires = '>=2.7',
)

