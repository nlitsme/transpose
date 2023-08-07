#!/usr/bin/python3
"""
Tool for transforming a row/column formatted set of data.
The default action is to transpose ( swap rows with columns )

You can also rotate the data over any multiple of 45 degrees.

Several ways of defining what consists a 'column':
    * fixed width
    * separator pattern
    * column pattern
    * separator with quoted strings.

Author: Willem Hengeveld <itsme@xs4all.nl>  (C) 2019

TODO: handle multiline quoted values.
TODO: add option to specify regex extracting columns from entire line.
TODO: add option to left/right-align columns in the output.
TODO: add option to retain separators with their column value.
      -- you can already kind of do this using the --pattern option.
"""
from __future__ import division, print_function
import re
import unittest
import itertools


def transform(m, b, n):
    """
    Given vector 'b', Calculate vector 'a' such that:
             2*a-n*one == M * (2*b-n*one),   where 'one' = (1, 1)
        --> a = M*b + (I-M)*one*n/2

    M is the transformation matrix,
    the coordinates of 'a' and 'b' range from 0 to n-1.
    """
    bb = []
    for j in range(len(b)):
        bb.append(2*b[j]-n)

    a = []
    for i in range(len(m)):
        x = 0
        for j in range(len(b)):
            x += m[i][j]*(2*b[j]-n)
        a.append(x)
    aa = []
    for j in range(len(a)):
        aa.append((a[j]+n)//2)

    return tuple(aa)


def gentransforms(n):
    """
    generate all n-dimensional transforms: rotations, flips, transpose, etc.
    """
    def genbits(i):
        while True:
            yield 2*(i&1)-1
            i >>= 1

    for p in itertools.permutations(range(n)):
        for i in range(pow(2, n)):
            b = genbits(i)
            yield [ [ next(b) if p[j] == _ else 0 for _ in range(n) ] for j in range(n) ]


def applytransformation(m, g):
    """
    Apply transformation 'm' to grid 'g'
    """
    h = len(g)
    w = len(g[0]) if g else 0
    res = [ [ None for _ in range(h) ] for _ in range(w) ]
    for y in range(h):
        for x in range(w):
            (a, b) = transform(m, (x, y), max(w, h)-1)
            res[b][a] = g[y][x]
    return res



def parsequoted(args, line):
    """
    Split a line containing quoted strings into columns.
    """
    fields = []
    rs = re.compile(args.separator)
    dquotes = '|""' if args.dquoted else ''
    squotes = "|''" if args.dquoted else ''
    rqq = re.compile(r'"(?:[^"\\]|\\(?:x\w{2}|u\w{4}|U\w{8}|u\{\w+\}|[^xuU])%s)*"' % dquotes)
    rq = re.compile(r'\'(?:[^\'\\]|\\(?:x\w{2}|u\w{4}|U\w{8}|u\{\w+\}|[^xuU])%s)*\'' % squotes)
    o = 0
    needseparator = False

    while o < len(line):
        if needseparator:
            m = rs.match(line, o)
            if not m:
                raise Exception("expected separator at pos %d in %s" % (o, line))
            o += len(m.group(0))
            needseparator = False
            continue
        m = rqq.match(line, o)
        if m:
            fields.append(m.group(0))
            o += len(m.group(0))
            needseparator = True
            continue
        m = rq.match(line, o)
        if m:
            fields.append(m.group(0))
            o += len(m.group(0))
            needseparator = True
            continue
        m = rs.search(line, o)
        if m:
            fields.append(line[o:m.start(0)])
            o = m.end(0)
        else:
            fields.append(line[o:])
            break
    return fields


class TestQUoted(unittest.TestCase):
    def testQuoted(self):
        class X: pass
        args = X()
        args.separator = ","
        args.dquoted = False

        self.assertEqual(parsequoted(args, "a,b,c"), [ "a", "b", "c" ])
        self.assertEqual(parsequoted(args, "a,\"b\",c"), [ "a", "\"b\"", "c" ])
        self.assertEqual(parsequoted(args, "a,\"b,x,y\",c"), [ "a", "\"b,x,y\"", "c" ])
        self.assertEqual(parsequoted(args, "a,\"b,\\n\",c"), [ "a", "\"b,\\n\"", "c" ])
        self.assertEqual(parsequoted(args, "a,\"b\nd\",c"), [ "a", "\"b\nd\"", "c" ])
        self.assertEqual(parsequoted(args, "a,\"b'd\",c"), [ "a", "\"b'd\"", "c" ])
        self.assertEqual(parsequoted(args, "a,\"b\\\"d\",c"), [ "a", "\"b\\\"d\"", "c" ])

        self.assertEqual(parsequoted(args, "a,'b',c"), [ "a", "'b'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b,x,y',c"), [ "a", "'b,x,y'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b,\\n',c"), [ "a", "'b,\\n'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b\nd',c"), [ "a", "'b\nd'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b\"d',c"), [ "a", "'b\"d'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b\\'d',c"), [ "a", "'b\\'d'", "c" ])

    def testDQuoted(self):
        class X: pass
        args = X()
        args.separator = ","
        args.dquoted = True

        self.assertEqual(parsequoted(args, "a,b,c"), [ "a", "b", "c" ])
        self.assertEqual(parsequoted(args, "a,'b',c"), [ "a", "'b'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b,x,y',c"), [ "a", "'b,x,y'", "c" ])
        self.assertEqual(parsequoted(args, "a,'b''y',c"), [ "a", "'b''y'", "c" ])

def splitfixedwidthcolumns(args, line):
    """
    Split line into columns using the argument specified with --width

    Allow user to specify width of individual columns.
      *:1,5,6    -- first, second 5 resp 6, others: 1
      5,5,5,1,5  -- specify width of each column, 6th column is remainder of line.
    """

    def parsewidth(spec):
        v = spec.split(":")
        return tuple( None if _ == '*' else int(_) for _ in v )

    columnwidths = []
    defaultwidth = None
    for w in args.width.split(","):
        w = parsewidth(w)
        if len(w) == 2:
            c, w = w
            if c is None:
                defaultwidth = w
            else:
                if len(columnwidths) <= c:
                    columnwidths += [None] * (1+c-len(columnwidths))
                columnwidths[c] = w
        else:
            w, = w
            columnwidths.append(w)
            defaultwidth = w

    o = 0
    for w in columnwidths:
        if w is None:
            w = defaultwidth
        yield line[o:o+w]
        o += w

    yield line[o:]


def usecolumnpattern(args, line):
    """
    Split line into columns using the --pattern option
    """
    return re.findall(args.pattern, line)


def splitbyseparator(args, line):
    """
    Split line into columns using the --separator option
    """
    return re.split(args.separator, line)


def processline(args, line):
    """
    Splits a line into columns.

    Returns a list of values.
    """

    # optionally strip spaces from the start of the line.
    if not args.keepspaces:
        line = re.sub(r'^\s+', '', line)

    if args.width:
        return list(splitfixedwidthcolumns(args, line))
    if args.quoted or args.dquoted:
        return parsequoted(args, line)
    if args.pattern is not None:
        return usecolumnpattern(args, line)
    if args.separator:
        return splitbyseparator(args, line)
    raise Exception("Don't know how to split line into columns.")


def parsematrix(args, lines):
    """
    Decodes the inputlines into a list of list ( the matrix ).
    """
    return [ processline(args, _.rstrip("\r\n")) for _ in lines ]


def makesquare(m):
    """
    Adds empty values, making the matrix 'm' square shaped.
    """
    h = len(m)
    w = max(len(row) for row in m) if m else 0

    size = max(h, w)

    # first add more rows
    while len(m) < size:
        m += [ [] ]

    # then make all rows equal length
    for row in m:
        if len(row) < size:
            row += [""] * (size-len(row))


def makerectangular(m):
    """
    Adds empty values, making the matrix 'm' rectangular shaped.
    """
    w = max(len(row) for row in m) if m else 0

    # then make all rows equal length
    for row in m:
        if len(row) < w:
            row += [""] * (w-len(row))


def getoutputseparator(args):
    """
    Determine the output separator to use.

    TODO: use retained separator, or explicitly specified output-separator.
    """
    if args.separator == "":
        return args.separator
    elif len(args.separator) == 1:
        return args.separator
    else:
        return "\t"


def converttoskewedmatrix(m):
    """
    convert to a skewed diamond shape.

                 a
    a b c        d b
    d e f   ->   g e c
    g h i          h f
                     i
         
    """
    d = [ [ "" for _ in range(len(m)) ] for _ in range(2*len(m)-1) ]
    for y in range(1, 2*len(m)):
        for x in range(len(m)):
            if 0 <= y+x-len(m) < len(m):
                d[2*len(m)-y-1][x] = m[x][y+x-len(m)]
    return d


def converttodiamondmatrix(m):
    """
    Convert to a diamond shaped matrix.

                   a
    a b c         d b
    d e f   ->   g e c
    g h i         h f
                   i

    """
    d = [ [ "" for _ in range(len(m)*2-1) ] for _ in range(2*len(m)-1) ]
    for y in range(1, 2*len(m)):
        for x in range(len(m)):
            if 0 <= y+x-len(m) < len(m):
                d[2*len(m)-y-1][2*x+y-len(m)] = m[x][y+x-len(m)]
    return d


def rotatematrix(args, m):
    """
    Transform the matrix 'm' according to the specified commandline options.
    """
    transformations = list(gentransforms(2))
    diamond = False
    if args.rotate and args.rotate % 90:
        args.rotate -= 45
        diamond = True

    # note: xflip, yflip and transpose are handle by more optimized code in 'processfile'
    if args.xflip:
        t = transformations[2]
    elif args.yflip:
        t = transformations[1]
    elif args.rotate is None:
        t = transformations[7]   # transpose
    elif args.rotate % 360 == 0:
        t = transformations[3]
    elif (args.rotate-90) % 360 == 0:
        t = transformations[5]
    elif (args.rotate+90) % 360 == 0:
        t = transformations[6]
    elif (args.rotate-180) % 360 == 0:
        t = transformations[0]
    else:
        print("??")

    m = applytransformation(t, m)

    if not diamond:
        pass
    elif args.skew:
        m = converttoskewedmatrix(m)
    else:
        m = converttodiamondmatrix(m)

    return m

def outputmatrix(args, m):
    """
    Converts the matrix to a list of lines,
    formatted according to the options specified on the commandline.
    """
    separator = getoutputseparator(args)
    for row in m:
        yield separator.join(row)


def reverselines(args, fh):
    """
    Reverse each line individually
    """
    # TODO: retain separator
    separator = getoutputseparator(args)
    for line in fh:
        cols = processline(args, line.rstrip("\r\n"))
        yield separator.join(cols[::-1])

def transposematrix(m):
    h = len(m)
    w = len(m[0]) if m else 0
    res = [ [ None for _ in range(h) ] for _ in range(w) ]
    for y in range(h):
        for x in range(w):
            res[x][y] = m[y][x]
    return res


def processfile(args, fh):
    """
    Process lines from the filehandle.
    """
    if args.xflip:
        lines = fh.readlines()
        for line in lines[::-1]:
            print(line.rstrip("\n"))
    elif args.yflip:
        for line in reverselines(args, fh):
            print(line)
    else:
        lines = fh.readlines()
        m = parsematrix(args, lines)
        if args.rotate is None:
            makerectangular(m)
            m = transposematrix(m)
        else:
            makesquare(m)
            m = rotatematrix(args, m)

        for line in outputmatrix(args, m):
            print(line)


def run_tests(args):
    unittest.main(verbosity=args.verbose)


def main():
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='transform a matrix, default: transpose', prefix_chars='-+', epilog="""
Specify negative numbers using: --rotate=-45
""")
    parser.add_argument('--test', action='store_true', help='run unittest')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('-t', '--separator', type=str, help='column separator')
    parser.add_argument('-p', '--pattern', type=str, help='column pattern, example: \\s+\\w+')
    parser.add_argument('-w', '--width', type=str, help="""Fixed width columns, alow multiple widths.
            Either a comma separated list of widths, with the last value taken for the remaining columns. ( 5,1,1,10 )
            Optionally a width can be prefixed with a column number followed by a colon. ( 5:1,7:1,8 )""")
    parser.add_argument('-l', '--keepspaces', action='store_true', help='Leading whitespace is relevant')
    #parser.add_argument('-a', '--align', action='store_true', help='Re-Align columns')
    parser.add_argument('-q', '--quoted', action='store_true', help='Quoted strings with C style escapes ( using backslash )in columns.')
    parser.add_argument('-Q', '--dquoted', action='store_true', help='Quoted strings with SQL style escapes ( using repeated quotes ) in columns.')
    parser.add_argument('--yflip', '-y', action='store_true', help='reverse each line')
    parser.add_argument('--xflip', '-x', '--tac', action='store_true', help='like "tac", output lines in reverse order')
    parser.add_argument('--rotate', type=int, help='Rotate by multiple of 45 degrees', metavar='DEG')
    parser.add_argument('+180', '-180', dest='rotate', const=180, action='store_const', help='rotate by 180 degrees')
    parser.add_argument('+90', dest='rotate', const=90, action='store_const', help='rotate by 90 degrees counter-clockwise')
    parser.add_argument('-90', dest='rotate', const=-90, action='store_const', help='rotate by 90 degrees clockwise')
    parser.add_argument('+45', dest='rotate', const=45, action='store_const', help='rotate by 45 degrees counter-clockwise')
    parser.add_argument('-45', dest='rotate', const=-45, action='store_const', help='rotate by 45 degrees clockwise')
    parser.add_argument('--skew', action='store_true', help='rotate by 45 degrees clockwise, but de-indent')
    parser.add_argument('input', metavar='DAT', type=str, nargs='*')
    args = parser.parse_args()

    if args.width and args.separator is None:
        args.separator = ""
    if args.pattern is None and args.separator is None:
        args.separator = "\t|,\\s*| +"
    if args.pattern is not None and args.separator is None:
        args.separator = ""
    if args.pattern:
        args.keepspaces = True

    if args.test:
        del sys.argv[1:]
        run_tests(args)

    if args.input:
        for fn in args.input:
            print("==> %s <==" % fn)
            with open(fn) as fh:
                processfile(args, fh)
    else:
        processfile(args, sys.stdin)


if __name__ == '__main__':
    main()
