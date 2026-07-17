#!/usr/bin/python3
"""
Transform row/column formatted data. Default action: transpose
(swap rows with columns).

Rotations over multiples of 45 degrees are supported; 45-degree
rotations produce a diamond layout, or a skewed layout with --skew.

Ways of defining what constitutes a 'column':
    * fixed width                    (-w)
    * separator pattern              (-t)
    * column pattern                 (-p)
    * separator with quoted strings  (-q / -Q)

Author: Willem Hengeveld <itsme@xs4all.nl>  (C) 2019

TODO: handle multiline quoted values.
TODO: add option to left/right-align columns in the output.
TODO: add option to retain separators with their column value.

several improvements by claude
"""
import re
import sys
import unittest


# ---------------- line -> columns ----------------

def parsequoted(args, line):
    """
    Split a line containing quoted strings into columns.
    Quotes are retained in the field values.
    """
    rs = re.compile(args.separator)
    dq = '|""' if args.dquoted else ''
    sq = "|''" if args.dquoted else ''
    rqq = re.compile(r'"(?:[^"\\]|\\(?:x\w{2}|u\w{4}|U\w{8}|u\{\w+\}|[^xuU])%s)*"' % dq)
    rq  = re.compile(r"'(?:[^'\\]|\\(?:x\w{2}|u\w{4}|U\w{8}|u\{\w+\}|[^xuU])%s)*'" % sq)

    fields = []
    o = 0
    needseparator = False
    while o < len(line):
        if needseparator:
            m = rs.match(line, o)
            if not m:
                raise ValueError("expected separator at pos %d in %r" % (o, line))
            if m.end() == o:
                raise ValueError("separator pattern matches the empty string")
            o = m.end()
            needseparator = False
            if o == len(line):
                fields.append("")            # line ends on a separator
            continue
        m = rqq.match(line, o) or rq.match(line, o)
        if m:
            fields.append(m.group())
            o = m.end()
            needseparator = True
            continue
        m = rs.search(line, o)
        if m:
            if m.end() == m.start() == o:
                raise ValueError("separator pattern matches the empty string")
            fields.append(line[o:m.start()])
            o = m.end()
            if o == len(line):
                fields.append("")            # line ends on a separator
        else:
            fields.append(line[o:])
            break
    return fields


def splitfixedwidthcolumns(args, line):
    """
    Split 'line' into fixed width columns as specified with --width.

      5,5,5,1     -- explicit widths; the remainder of the line becomes
                     one final column.
      5:1,7:1,8   -- width 1 for columns 5 and 7; the bare width fills
                     the unspecified columns; remainder as above.
      2,3,*:8     -- two explicit columns, then repeat width 8 until
                     the line is consumed.
    """
    def parsewidth(spec):
        v = spec.split(":")
        return tuple(None if _ == '*' else int(_) for _ in v)

    columnwidths = []
    defaultwidth = None
    repeat = False
    for w in args.width.split(","):
        w = parsewidth(w)
        if len(w) == 2:
            c, w = w
            if c is None:
                defaultwidth = w
                repeat = True
            else:
                if len(columnwidths) <= c:
                    columnwidths += [None] * (1 + c - len(columnwidths))
                columnwidths[c] = w
        else:
            w, = w
            columnwidths.append(w)
            defaultwidth = w

    o = 0
    for w in columnwidths:
        if w is None:
            w = defaultwidth
        yield line[o:o + w]
        o += w
    if repeat:
        while o < len(line):
            yield line[o:o + defaultwidth]
            o += defaultwidth
    else:
        yield line[o:]


def processline(args, line):
    """Split a line into a list of column values."""
    # leading whitespace is part of the layout in fixed width mode
    if not args.keepspaces and not args.width:
        line = re.sub(r'^\s+', '', line)

    if args.width:
        return list(splitfixedwidthcolumns(args, line))
    if args.quoted or args.dquoted:
        return parsequoted(args, line)
    if args.pattern is not None:
        return re.findall(args.pattern, line)
    if args.separator:
        return re.split(args.separator, line)
    raise ValueError("don't know how to split line into columns")


def parsematrix(args, lines):
    """Decode the input lines into a list of lists (the matrix)."""
    return [processline(args, _.rstrip("\r\n")) for _ in lines]


# ---------------- shape helpers ----------------

def makerectangular(m):
    """Pad rows with empty values so all rows have equal length."""
    w = max(len(row) for row in m) if m else 0
    for row in m:
        if len(row) < w:
            row += [""] * (w - len(row))


def makesquare(m):
    """Pad the matrix with empty values into a square shape."""
    h = len(m)
    w = max(len(row) for row in m) if m else 0
    size = max(h, w)
    while len(m) < size:
        m.append([])
    for row in m:
        if len(row) < size:
            row += [""] * (size - len(row))


# ---------------- transformations ----------------

def transposematrix(m):
    return [list(row) for row in zip(*m)] if m else m


def converttoskewedmatrix(m):
    """
                 a
    a b c        d b
    d e f   ->   g e c
    g h i          h f
                     i
    """
    d = [["" for _ in range(len(m))] for _ in range(2 * len(m) - 1)]
    for y in range(1, 2 * len(m)):
        for x in range(len(m)):
            if 0 <= y + x - len(m) < len(m):
                d[2 * len(m) - y - 1][x] = m[x][y + x - len(m)]
    return d


def converttodiamondmatrix(m):
    """
                   a
    a b c         d b
    d e f   ->   g e c
    g h i         h f
                   i
    """
    d = [["" for _ in range(2 * len(m) - 1)] for _ in range(2 * len(m) - 1)]
    for y in range(1, 2 * len(m)):
        for x in range(len(m)):
            if 0 <= y + x - len(m) < len(m):
                d[2 * len(m) - y - 1][2 * x + y - len(m)] = m[x][y + x - len(m)]
    return d


def rotatematrix(args, m):
    """
    Rotate the rectangular matrix 'm' over args.rotate degrees
    (counter-clockwise for positive angles). Does not modify args.
    """
    rot = args.rotate
    if rot % 45:
        raise ValueError("rotation must be a multiple of 45 degrees")
    diamond = bool(rot % 90)
    if diamond:
        rot -= 45
        makesquare(m)          # only the diamond layouts need a square

    r = rot % 360
    if r == 90:
        m = transposematrix(m)[::-1]
    elif r == 180:
        m = [row[::-1] for row in m[::-1]]
    elif r == 270:
        m = [row[::-1] for row in transposematrix(m)]

    if not diamond or not m:
        return m
    return converttoskewedmatrix(m) if args.skew else converttodiamondmatrix(m)


# ---------------- output ----------------

def getoutputseparator(args):
    """Explicit -o wins; else reuse a literal separator; else tab."""
    outsep = getattr(args, 'outsep', None)
    if outsep is not None:
        return outsep
    if not args.separator:
        return ""
    if len(args.separator) == 1:
        return args.separator
    return "\t"


def outputmatrix(args, m):
    """Format the matrix as lines, trimming trailing empty cells."""
    separator = getoutputseparator(args)
    for row in m:
        n = len(row)
        while n and row[n - 1] == "":
            n -= 1
        yield separator.join(row[:n])


def reverselines(args, fh):
    """Reverse the columns of each line individually."""
    separator = getoutputseparator(args)
    for line in fh:
        cols = processline(args, line.rstrip("\r\n"))
        yield separator.join(cols[::-1])


def processfile(args, fh):
    if args.xflip:
        for line in fh.readlines()[::-1]:
            print(line.rstrip("\r\n"))
    elif args.yflip:
        for line in reverselines(args, fh):
            print(line)
    else:
        m = parsematrix(args, fh.readlines())
        makerectangular(m)
        if args.rotate is None:
            m = transposematrix(m)
        else:
            m = rotatematrix(args, m)
        for line in outputmatrix(args, m):
            print(line)


# ---------------- tests ----------------

class Opts:
    """Minimal stand-in for parsed arguments in tests."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TestQuoted(unittest.TestCase):
    def testQuoted(self):
        args = Opts(separator=",", dquoted=False)
        self.assertEqual(parsequoted(args, "a,b,c"), ["a", "b", "c"])
        self.assertEqual(parsequoted(args, 'a,"b",c'), ["a", '"b"', "c"])
        self.assertEqual(parsequoted(args, 'a,"b,x,y",c'), ["a", '"b,x,y"', "c"])
        self.assertEqual(parsequoted(args, 'a,"b,\\n",c'), ["a", '"b,\\n"', "c"])
        self.assertEqual(parsequoted(args, 'a,"b\nd",c'), ["a", '"b\nd"', "c"])
        self.assertEqual(parsequoted(args, 'a,"b\'d",c'), ["a", '"b\'d"', "c"])
        self.assertEqual(parsequoted(args, 'a,"b\\"d",c'), ["a", '"b\\"d"', "c"])
        self.assertEqual(parsequoted(args, "a,'b',c"), ["a", "'b'", "c"])
        self.assertEqual(parsequoted(args, "a,'b,x,y',c"), ["a", "'b,x,y'", "c"])
        self.assertEqual(parsequoted(args, "a,'b,\\n',c"), ["a", "'b,\\n'", "c"])
        self.assertEqual(parsequoted(args, "a,'b\nd',c"), ["a", "'b\nd'", "c"])
        self.assertEqual(parsequoted(args, "a,'b\"d',c"), ["a", "'b\"d'", "c"])
        self.assertEqual(parsequoted(args, "a,'b\\'d',c"), ["a", "'b\\'d'", "c"])

    def testTrailing(self):
        args = Opts(separator=",", dquoted=False)
        self.assertEqual(parsequoted(args, "a,b,"), ["a", "b", ""])
        self.assertEqual(parsequoted(args, "a,'b',"), ["a", "'b'", ""])
        self.assertEqual(parsequoted(args, "a,,b"), ["a", "", "b"])

    def testDQuoted(self):
        args = Opts(separator=",", dquoted=True)
        self.assertEqual(parsequoted(args, "a,b,c"), ["a", "b", "c"])
        self.assertEqual(parsequoted(args, "a,'b',c"), ["a", "'b'", "c"])
        self.assertEqual(parsequoted(args, "a,'b,x,y',c"), ["a", "'b,x,y'", "c"])
        self.assertEqual(parsequoted(args, "a,'b''y',c"), ["a", "'b''y'", "c"])


class TestTransforms(unittest.TestCase):
    M = [list("ab"), list("cd"), list("ef")]                 # 3 rows x 2 cols

    def rot(self, m, deg, skew=False):
        return rotatematrix(Opts(rotate=deg, skew=skew),
                            [row[:] for row in m])

    def testTranspose(self):
        self.assertEqual(transposematrix(self.M), [list("ace"), list("bdf")])
        self.assertEqual(transposematrix(transposematrix(self.M)), self.M)

    def testRectangularRotations(self):
        self.assertEqual(self.rot(self.M, 90), [list("bdf"), list("ace")])
        self.assertEqual(self.rot(self.rot(self.M, 90), 90),
                         self.rot(self.M, 180))
        self.assertEqual(self.rot(self.rot(self.M, 90), 270), self.M)
        self.assertEqual(self.rot(self.M, -90), self.rot(self.M, 270))

    def testDiamond(self):
        self.assertEqual(self.rot([list("ab"), list("cd")], 45),
                         [["", "b", ""], ["a", "", "d"], ["", "c", ""]])

    def testBadAngle(self):
        with self.assertRaises(ValueError):
            self.rot(self.M, 30)


# ---------------- main ----------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='transform a matrix, default: transpose',
        prefix_chars='-+',
        epilog='Specify negative numbers using: --rotate=-45')
    parser.add_argument('--test', action='store_true', help='run unittests')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('-t', '--separator', type=str,
                        help='column separator (regex)')
    parser.add_argument('-p', '--pattern', type=str,
                        help='column pattern, example: \\s+\\w+')
    parser.add_argument('-w', '--width', type=str,
                        help='fixed width columns: comma separated widths, '
                             'remainder becomes the last column; N:W sets '
                             'column N only; *:W repeats width W to the end '
                             'of the line')
    parser.add_argument('-l', '--keepspaces', action='store_true',
                        help='leading whitespace is relevant')
    parser.add_argument('-q', '--quoted', action='store_true',
                        help='quoted strings with C style (backslash) escapes')
    parser.add_argument('-Q', '--dquoted', action='store_true',
                        help='quoted strings with SQL style (doubled quote) escapes')
    parser.add_argument('-o', '--output-separator', dest='outsep', type=str,
                        help='separator used between output columns')
    parser.add_argument('--yflip', '-y', action='store_true',
                        help='reverse each line')
    parser.add_argument('--xflip', '-x', '--tac', action='store_true',
                        help='like "tac", output lines in reverse order')
    parser.add_argument('--rotate', type=int, metavar='DEG',
                        help='rotate by a multiple of 45 degrees')
    parser.add_argument('+180', '-180', dest='rotate', const=180,
                        action='store_const', help='rotate by 180 degrees')
    parser.add_argument('+90', dest='rotate', const=90, action='store_const',
                        help='rotate by 90 degrees counter-clockwise')
    parser.add_argument('-90', dest='rotate', const=-90, action='store_const',
                        help='rotate by 90 degrees clockwise')
    parser.add_argument('+45', dest='rotate', const=45, action='store_const',
                        help='rotate by 45 degrees counter-clockwise')
    parser.add_argument('-45', dest='rotate', const=-45, action='store_const',
                        help='rotate by 45 degrees clockwise')
    parser.add_argument('--skew', action='store_true',
                        help='with 45 degree rotations: skewed layout instead of diamond')
    parser.add_argument('input', metavar='DAT', type=str, nargs='*')
    args = parser.parse_args()

    if args.rotate is not None and args.rotate % 45:
        parser.error("--rotate must be a multiple of 45 degrees")

    if args.width and args.separator is None:
        args.separator = ""
    if args.pattern is None and args.separator is None:
        args.separator = "\t|,\\s*| +"
    if args.pattern is not None and args.separator is None:
        args.separator = ""
    if args.pattern:
        args.keepspaces = True

    if args.test:
        sys.argv[1:] = []
        unittest.main(verbosity=args.verbose)

    if args.input:
        for fn in args.input:
            print("==> %s <==" % fn)
            with open(fn) as fh:
                processfile(args, fh)
    else:
        processfile(args, sys.stdin)


if __name__ == '__main__':
    main()

