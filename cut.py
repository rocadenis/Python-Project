
import sys
import argparse

VERSION = "cut.py 1.0"

def parse_list(list_str):
    ranges = []
    for part in list_str.split(','):
        part = part.strip()
        if '-' in part:
            start_str, end_str = part.split('-', 1)
            if start_str == '' and end_str == '':
                continue
            if start_str == '':
                end = int(end_str)
                start = 1
            elif end_str == '':
                start = int(start_str)
                end = None
            else:
                start = int(start_str)
                end = int(end_str)
            ranges.append((start, end))
        else:
            val = int(part)
            ranges.append((val, val))
    return ranges

def build_selection(ranges, length):
    selection = set()
    for (start, end) in ranges:
        if end is None:
            end = length
        end = min(end, length)
        if start <= end <= length:
            selection.update(range(start, end+1))
        elif start <= length and end is None:
            selection.update(range(start, length+1))
    return selection

def complement_selection(selection, length):
    full = set(range(1, length+1))
    return full - selection

def process_bytes(line, ranges, complement=False):
    b_line = line.encode('utf-8', 'replace')
    length = len(b_line)
    selection = build_selection(ranges, length)
    if complement:
        selection = complement_selection(selection, length)
    result_bytes = bytearray([b_line[i-1] for i in sorted(selection)])
    return result_bytes.decode('utf-8', 'replace')

def process_chars(line, ranges, complement=False):
    length = len(line)
    selection = build_selection(ranges, length)
    if complement:
        selection = complement_selection(selection, length)
    return ''.join(line[i-1] for i in sorted(selection))

def process_fields(line, ranges, delimiter='\t', output_delimiter=None, only_delimited=False, complement=False):
    fields = line.split(delimiter)
    length = len(fields)
    if length == 1 and delimiter not in line:
        if only_delimited:
            return None
        else:
            return line
    selection = build_selection(ranges, length)
    if complement:
        selection = complement_selection(selection, length)
    selected_fields = [fields[i-1] for i in sorted(selection) if 1 <= i <= length]
    if output_delimiter is None:
        output_delimiter = delimiter
    return output_delimiter.join(selected_fields)

def main():
    parser = argparse.ArgumentParser(description="cut command implementation", add_help=False)
    parser.add_argument('-b', '--bytes', help="Select only these bytes.")
    parser.add_argument('-c', '--characters', help="Select only these characters.")
    parser.add_argument('-d', '--delimiter', help="Use DELIM instead of TAB for field delimiter.", default=None)
    parser.add_argument('-f', '--fields', help="Select only these fields.")
    parser.add_argument('-n', action='store_true', help="Ignored.")
    parser.add_argument('--complement', action='store_true', help="Complement the set of selected bytes, characters or fields.")
    parser.add_argument('-s', '--only-delimited', action='store_true', help="Do not print lines that do not contain delimiters.")
    parser.add_argument('--output-delimiter', help="Use STRING as the output delimiter.")
    parser.add_argument('-z', '--zero-terminated', action='store_true', help="Use NULL as line delimiter, not newline.")
    parser.add_argument('--help', action='store_true', help="Display this help and exit.")
    parser.add_argument('--version', action='store_true', help="Output version information and exit.")
    parser.add_argument('files', nargs='*', help="Input files (or - for stdin)")

    args = parser.parse_args()

    if args.help:
        parser.print_help(sys.stdout)
        sys.exit(0)
    if args.version:
        print(VERSION)
        sys.exit(0)

    if not (args.bytes or args.characters or args.fields):
        sys.stderr.write("Error: You must specify one of -b, -c or -f.\n")
        sys.exit(1)

    delimiter = args.delimiter if args.delimiter is not None else '\t'
    output_delimiter = args.output_delimiter
    complement = args.complement
    only_delimited = args.only_delimited
    zero_terminated = args.zero_terminated

    byte_ranges = parse_list(args.bytes) if args.bytes else None
    char_ranges = parse_list(args.characters) if args.characters else None
    field_ranges = parse_list(args.fields) if args.fields else None

    if len(args.files) == 0:
        files = [sys.stdin]
    else:
        input_files = []
        for f in args.files:
            if f == '-':
                input_files.append(sys.stdin)
            else:
                try:
                    input_files.append(open(f, 'r', newline=''))
                except IOError as e:
                    sys.stderr.write(f"Error opening file {f}: {e}\n")
                    sys.exit(1)
        files = input_files

    line_terminator = '\0' if zero_terminated else '\n'

    try:
        for f in files:
            if zero_terminated:
                content = f.read()
                lines = content.split('\0')
                if lines and lines[-1] == '':
                    lines.pop()
            else:
                lines = f.read().split('\n')
                if lines and lines[-1] == '':
                    lines.pop()

            for line in lines:
                if args.bytes:
                    processed = process_bytes(line, byte_ranges, complement=complement)
                elif args.characters:
                    processed = process_chars(line, char_ranges, complement=complement)
                elif args.fields:
                    processed = process_fields(line, field_ranges, delimiter=delimiter,
                                               output_delimiter=output_delimiter,
                                               only_delimited=only_delimited,
                                               complement=complement)
                if processed is not None:
                    sys.stdout.write(processed)
                    sys.stdout.write(line_terminator)
    finally:
        for ff in files:
            if ff is not sys.stdin:
                ff.close()

if __name__ == '__main__':
    main()
