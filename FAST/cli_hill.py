import os
import sys
import argparse
import warnings

from FAST import hill

def main():
    warnings.filterwarnings("ignore")

    usage = ['%(prog)s -d [FILE]',
             '------------------------------------------------------------------------',
             'Hill: Hill equation fit for pCa vs. speed data',
             '',
             'Reads a CSV or Excel (.xlsx/.xls) file with "pCa" and "speed" columns.',
             'Duplicate pCa values are averaged before fitting.',
             'Outputs a goodness-of-fit text file and a plot (PDF + PNG),',
             'both named after the folder that contains the input file.',
             '------------------------------------------------------------------------']

    parser = argparse.ArgumentParser(description='', usage='\n'.join(usage))
    parser.add_argument('-d', help='CSV or Excel file with pCa and speed columns', required=True)
    args = parser.parse_args()
    parser.print_help()

    if not os.path.isfile(args.d):
        sys.exit(f"\nFile not found: {args.d}")

    hill.run_hill_fit(args.d)

if __name__ == "__main__":
    main()
