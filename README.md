# transpose

Command line tool for transforming row/column formatted textual data.
The default action is to transpose a table: swap its rows and columns.
You can also rotate by multiples of 45 degrees, reverse line order,
or reverse the columns within each line.

Columns can be defined by fixed widths, a separator regular expression,
a regular expression matching each field, or separators with quoted fields.
Values remain text; quotes and escape sequences are preserved.

## Install

The script requires Python 3 and uses only the standard library:

```sh
python3 transpose.py --help
```

The project is also packaged as `text-transpose`:

```sh
pip install text-transpose
```

The examples below use the `transpose` command. When running the source
directly, replace it with `python3 transpose.py`. A published package may
have fewer options than the current script; check its `--help` output.

## Usage

```text
transpose [-h] [--test] [-v] [-t SEPARATOR] [-p PATTERN]
          [-w WIDTH] [-l] [-q] [-Q] [-o OUTSEP] [-y] [-x]
          [--rotate DEG] [+180] [+90] [-90] [+45] [-45] [--skew]
          [DAT ...]
```

With no filenames, input is read from standard input. With filenames, each
file is transformed independently and preceded by an `==> filename <==`
heading, even when only one file is supplied. Output goes to standard output.
Use input redirection to transform a file without a heading:

```sh
transpose < input.txt > output.txt
transpose first.txt second.txt
```

There is no special `-` filename for standard input. Files use Python's
default text encoding. Input line endings are removed; each output row is
written with a newline.

### Options

| Option | Meaning |
| --- | --- |
| `-t REGEX`, `--separator REGEX` | Split each line at matches of a separator regex. |
| `-p REGEX`, `--pattern REGEX` | Extract fields by matching a column regex. Unmatched text is discarded. |
| `-w SPEC`, `--width SPEC` | Split each line into fixed width fields; see below. |
| `-l`, `--keepspaces` | Preserve leading whitespace before splitting. |
| `-q`, `--quoted` | Recognize single- or double-quoted fields with backslash escapes. |
| `-Q`, `--dquoted` | Also recognize doubled quotes inside quoted fields. |
| `-o TEXT`, `--output-separator TEXT` | Join output fields with this literal string, including an empty string. |
| `-y`, `--yflip` | Reverse fields within each line. |
| `-x`, `--xflip`, `--tac` | Reverse input line order, preserving each line's contents. |
| `--rotate DEG` | Rotate counter-clockwise by a multiple of 45 degrees; negative angles rotate clockwise. |
| `+90`, `-90` | Rotate 90 degrees counter-clockwise or clockwise. |
| `+180`, `-180` | Rotate 180 degrees. |
| `+45`, `-45` | Rotate 45 degrees counter-clockwise or clockwise. |
| `--skew` | Use a compact skewed layout for rotations not divisible by 90. |
| `--test` | Run the built-in unit tests and exit. |
| `-v`, `--verbose` | Increase test verbosity; repeat for more detail. |
| `-h`, `--help` | Show command line help. |

Transformations are alternatives, not a pipeline: `-x` takes precedence over
`-y`, and `-y` takes precedence over rotation or transposition. `-x` does not
split fields or use the output separator. If several rotation options are
given, the last one wins. `--rotate 0` parses and reformats the input without
changing its orientation. `--skew` has no effect without a diagonal rotation.

For negative angles with the long option, use `--rotate=-45`.

## Defining columns

### Separator patterns

The default separator is `\t|,\s*| +`: a tab, a comma followed by optional
whitespace, or one or more ordinary spaces. Leading whitespace is removed
unless `-l` is given. Headers and blank lines receive no special treatment.

Use `-t` to select a different separator:

```sh
transpose -t ',' < comma-separated.txt
transpose -t '\s+' < whitespace-separated.txt
transpose -t '\|' < pipe-separated.txt
```

The argument is a Python regular expression, so metacharacters such as `|`
or `.` must be escaped when intended literally. Avoid capturing groups in
separator patterns: ordinary splitting includes their matches as fields.
Use non-capturing groups, `(?:...)`, when grouping is needed.

### Column patterns

`-p` uses Python's `re.findall` to extract fields rather than splitting at
separators. Leading whitespace is preserved automatically for nonempty
patterns. Text outside the matches is discarded.

```sh
printf 'x=12 y=34\nx=56 y=78\n' | transpose -p '\d+' -o ','
```

```text
12,56
34,78
```

Avoid capturing groups: one group returns only the captured text, while
multiple groups return tuples that cannot be formatted as output fields.
The `-t` argument can still set the default output separator in pattern mode;
`-o` is the clearer way to choose it explicitly.

### Fixed width columns

`-w` measures widths in Python string characters, not bytes or terminal
display cells. Leading whitespace is always preserved in this mode.

| Specification | Fields extracted from each line |
| --- | --- |
| `2,3` | Two characters, then three characters, then the entire remainder. |
| `2,3,*:8` | Two characters, then three characters, then repeated eight-character fields. |
| `*:1` | One character per field until the line ends. |
| `5:1,7:1,8` | Width one for columns 5 and 7; width eight for unspecified columns through column 8; then the remainder. |

Column indices in `N:W` are **zero-based**. An indexed entry sets that
column's width; a bare width appends a column and supplies the default width
for unspecified positions. `*:W` repeats width `W` after the explicitly
defined columns until the line is consumed. Use positive widths.

Without `*:W`, the remaining text becomes one final field, even when empty.
Short lines can produce short or empty fields.

```sh
printf 'abcdefghij\nklmnopqrst\n' | transpose -w 2,3 -o '|'
```

```text
ab|kl
cde|mno
fghij|pqrst
```

For example, fixed widths can transpose a long directory listing:

```sh
ls -al | transpose -w 10,5,6,7,7,12 -o ' | '
```

The widths depend on the actual `ls` output. Alternatively, extract
non-whitespace runs together with their following whitespace:

```sh
ls -al | transpose -p '\S+\s*' -o ','
```

### Quoted fields

Combine `-q` or `-Q` with a separator to keep delimiters inside quoted fields:

```sh
printf 'name,city\n"Doe, Jane","New York"\n' | transpose -t ',' -q -o '|'
```

```text
name|"Doe, Jane"
city|"New York"
```

Both modes recognize single and double quotes and backslash escapes.
`-Q` additionally recognizes doubled quotes, such as `"a""b"` or `'a''b'`.
Quotes and escape sequences are retained exactly; they are not decoded or
rewritten. A quote must begin at the start of a field to be recognized.
For comma-separated input with optional spaces after commas, use `-t ',\s*'`.

This is line-based parsing: quoted values spanning multiple input lines are
not supported. Output is joined literally, without adding quoting or escaping
for the chosen separator. The parser is not a strict CSV validator.
Use separator patterns that consume at least one character.

When splitting options are combined, fixed widths take precedence, followed
by quoted fields, column patterns, and ordinary separator splitting.

## Output and uneven rows

`-o` always selects the literal output separator. Without `-o`:

| Effective separator setting | Output separator |
| --- | --- |
| One-character `-t` argument | That character, even if it is a regex metacharacter. |
| Longer separator regex, including the default | Tab. |
| Fixed width or pattern mode with no `-t` | Empty string; fields are concatenated. |

Shell escape notation is not decoded by the tool. In Bash, use `-o $'\t'`
for a literal tab; `-o '\t'` emits a backslash followed by `t`.

Before transposition or rotation, shorter rows are padded with empty fields
to form a rectangle. Diagonal rotations additionally pad to a square whose
side is the larger input dimension. Empty input produces no data rows.

Trailing empty fields are removed from each output row after transposition
or rotation; leading and interior empty fields remain. A wholly empty row
becomes a blank line. `-y` reverses each line independently without padding
or trimming empty fields. Original separators are not retained after parsing.

Transposition, rotation, and line reversal read the whole input into memory.
Field reversal with `-y` processes one line at a time. Parsing and file errors
stop processing; there is no continue-on-error mode.

## Examples

### Swap rows and columns

```sh
printf 'a b c\nd e f\n' | transpose -o ' '
```

```text
a d
b e
c f
```

### Rotate a rectangle

```sh
printf 'a b c\nd e f\n' | transpose +90 -o ' '
```

```text
c f
b e
a d
```

With `-90`, the same input becomes:

```text
d a
e b
f c
```

### Rotate by 45 degrees

```sh
printf 'a b c\nd e f\ng h i\n' | transpose -45 -o ' '
```

```text
  a
 d  b
g  e  c
 h  f
  i
```

Add `--skew` to compact the layout:

```text
a
d b
g e c
 h f
  i
```

Empty cells provide the spacing; values are not padded to equal display
widths, so longer values can make diagonal layouts appear uneven.

### Reverse fields, characters, or lines

```sh
printf 'a b c\nd e f\n' | transpose -y -o ' '
```

```text
c b a
f e d
```

Reverse characters using a repeating width or a column pattern:

```sh
transpose -y -w '*:1'
transpose -y -p '.'
```

`-w 1` alone splits off one character and treats the remainder as one field;
it does not split the entire line into characters.

Reverse words separated by individual spaces:

```sh
transpose -y -t ' '
```

Reverse line order, like `tac`:

```sh
transpose -x
```

## Tests

```sh
python3 transpose.py --test -vv
```

The built-in tests cover quoted fields, empty fields, transposition,
rectangular rotations, diamond layouts, and invalid rotation angles.

## TODO

* Handle multiline quoted values.
* Add left/right alignment of output columns.
* Add an option to retain separators with their column values.
  The `--pattern` option can already retain matching whitespace or separators.
* Quoting and escaping are deliberately left intact. Rewriting these is
  better handled by a separate tool.

## Author

Willem Hengeveld <itsme@xs4all.nl>
