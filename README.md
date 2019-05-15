# transpose
Command line tool for transforming row/column formatted textual data.

The default action is to transpose ( swap rows with columns ).

You can also rotate the data over any multiple of 45 degrees.

Several ways of defining what consists a 'column':
    * fixed width
    * separator pattern
    * column pattern
    * separator with quoted strings.

Either takes data from stdin, or uses the files specified on the commandline.

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
      -a, --align           Re-Align columns
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

# Author
Willem Hengeveld <itsme@xs4all.nl> 
