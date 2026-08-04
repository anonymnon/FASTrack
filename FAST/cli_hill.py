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
             '',
             'Pass -d2 to fit and plot a second file on the same graph, each',
             'with its own independent fit (default: -d in black, -d2 in red).',
             '------------------------------------------------------------------------']

    parser = argparse.ArgumentParser(description='', usage='\n'.join(usage))
    parser.add_argument('-d',    help='CSV or Excel file with pCa and speed columns', required=True)
    parser.add_argument('-d2',   help='Optional second CSV or Excel file to fit and plot alongside -d', default=None)
    parser.add_argument('-c',    help='Name of the speed column for -d (Default: speed)', default='speed')
    parser.add_argument('-p',    help='Name of the pCa column for -d (Default: pCa)', default='pCa')
    parser.add_argument('-c2',   help='Name of the speed column for -d2 (Default: same as -c)', default=None)
    parser.add_argument('-p2',   help='Name of the pCa column for -d2 (Default: same as -p)', default=None)
    parser.add_argument('-col1', help='Line/marker color for -d when -d2 is also given (Default: black)', default='black')
    parser.add_argument('-col2', help='Line/marker color for -d2 (Default: red)', default='red')
    parser.add_argument('-bs', action='store_true', default=False,
                        help='Subtract pCa 9 mean speed as baseline so no-calcium speed = 0 (applies to -d2 as well when given; ignored if -nl is given)')
    parser.add_argument('-nl', action='store_true', default=False,
                        help='Normalize each curve to its own min/max speed (0-1 scale) before fitting/plotting - the minimum and maximum are taken per curve, not shared across -d/-d2. Ignores -bs. Output files get a "_nl" suffix')
    parser.add_argument('-fixmin', action='store_true', default=False,
                        help='Use pCa 9 as the zero baseline (implies -bs, even if -bs isn\'t separately given) and fix Smin at exactly 0 in the fit (a 3-parameter fit over Smax/Ca50/n) so the fitted curve passes through 0 there, instead of leaving Smin as a free parameter that only approximately reaches 0. Applies to -d2 as well when given.')
    args = parser.parse_args()
    parser.print_help()

    if not os.path.isfile(args.d):
        sys.exit(f"\nFile not found: {args.d}")

    if args.nl and args.bs:
        print("Note: -bs is ignored because -nl was given (normalization already zeroes the baseline).")

    if args.d2:
        if not os.path.isfile(args.d2):
            sys.exit(f"\nFile not found: {args.d2}")
        hill.run_hill_fit_compare(args.d, args.d2, speed_col=args.c, pca_col=args.p,
                                   speed_col2=args.c2, pca_col2=args.p2,
                                   baseline_subtract=args.bs,
                                   color1=args.col1, color2=args.col2,
                                   normalize=args.nl, fix_smin=args.fixmin)
    else:
        hill.run_hill_fit(args.d, speed_col=args.c, pca_col=args.p,
                           baseline_subtract=args.bs, normalize=args.nl, fix_smin=args.fixmin)

if __name__ == "__main__":
    main()
