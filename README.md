# transpose
Command line tool for transforming row/column formatted textual data.

Often you have data formatted in rows and columns in some way, this tool
allows one to specify how your data in each line is organised in columns.
`transpose` can transform the matrix formed by the columns and rows in
several ways. You can transpose, rotate by multiples of 45 or 90 degrees.
Or flip the data vertically, or horizontally.

The default action is to transpose ( swap rows with columns ).

Several ways of defining what consists a 'column':

* fixed width columns.
* using a separator pattern, default: '`\t|,\s*| +`'
  - TAB or COMMA followed by optional whitespace or SPACES
* by a column pattern, example: '`\s+\w+`'
* separator with quoted strings, often used in CSV files.

In the output the separator is either the single character separator specified with the `-t` option,
or, when the separator is a pattern, a TAB charater is used.

Data is either read from stdin, or from files specified on the commandline.

# Install

You can instal `transpose` from [pypi](https://pypi.org/project/text-transpose/1.0.0/) using `pip`:

    pip install text-transpose

# Usage

    usage: transpose.py [-h] [--test] [--verbose] [-t SEPARATOR] [-p PATTERN]
                        [-w WIDTH] [-l] [-a] [-q] [-Q] [--yflip] [--xflip]
                        [--rotate DEG] [+180] [+90] [-90] [+45] [-45] [--skew]
                        [DAT [DAT ...]]

    transform a matrix, default: transpose

    positional arguments:
      DAT

    optional arguments:
      -h, --help            show this help message and exit
      --test                run unittest
      --verbose, -v
      -t SEPARATOR, --separator SEPARATOR
                            column separator
      -p PATTERN, --pattern PATTERN
                            column pattern, example: \s+\w+
      -w WIDTH, --width WIDTH
                            Fixed width columns, alow multiple widths. Either a
                            comma separated list of widths, with the last value
                            taken for the remaining columns. ( 5,1,1,10 )
                            Optionally a width can be prefixed with a column
                            number followed by a colon. ( 5:1,7:1,8 )
      -l, --keepspaces      Leading whitespace is relevant
      -q, --quoted          Quoted strings with C style escapes ( using backslash
                            )in columns.
      -Q, --dquoted         Quoted strings with SQL style escapes ( using repeated
                            quotes ) in columns.
      --yflip, -y           reverse each line
      --xflip, -x, --tac    like "tac", output lines in reverse order
      --rotate DEG          Rotate by multiple of 45 degrees
      +180, -180            rotate by 180 degrees
      +90                   rotate by 90 degrees counter-clockwise
      -90                   rotate by 90 degrees clockwise
      +45                   rotate by 45 degrees counter-clockwise
      -45                   rotate by 45 degrees clockwise
      --skew                rotate by 45 degrees clockwise, but de-indent

    Specify negative numbers using: --rotate=-45


# Example

## split the output of `ls` into columns, and transpose:

    ls -al | transpose -w 10,5,6,7,7,12

NOTE: this depends on the actual rendering by `ls`, column widths may vary.

Alternatively, you could split the output of `ls` into columns using:

    ls -al | transpose -p "\S+\s*" -t,

## Swap columns and rows:

    cat <<__EOF__ | transpose
    a b c
    d e f
    __EOF__

Will result in:

    a   d   
    b   e   
    c   f   

## Rotate by 45 degrees

    cat <<__EOF__ | transpose -45
    a b c
    d e f
    g h i
    __EOF__

Results in:

            a       
        d       b   
    g       e       c
        h       f   
            i       


## reverse column order

    cat <<__EOF__ | transpose -y
    a b c
    d e f
    __EOF__

Will result in:

    c   b   a
    f   e   d

## reverse a line

    transpose -y -w 1
    transpose -y -p .

## reverse words in a line

    transpose -y -t " "

## reverse a list of lines

Like `tac`:

    transpose -x

# TODO

 * Handle multiline quoted values.
 * Add option to specify regex extracting columns from entire line.
 * Add option to left/right-align columns in the output.
 * Add option to retain separators with their column value.
   - you can already kind of do this using the --pattern option.
 * I thought about adding options to change the way values are quoted, and separated,
   now i think that is better left to a different tool. So for now i will just leave
   the quoting and escaping intact, like it is.
 * Add option to specify an output separator.

# Author
Willem Hengeveld <itsme@xs4all.nl> 
