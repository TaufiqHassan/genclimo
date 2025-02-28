import time
import argparse
from src.get_climoFiles import get_climo


def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Process climate data.")

    parser.add_argument("-c", "--case", help="Case name", required=True)
    parser.add_argument("-s", "--start", help="Start year", required=True)
    parser.add_argument("-e", "--end", help="End year", default=None)
    parser.add_argument("-indir", "--input_dir", help="Input directory", default=None)
    parser.add_argument("-outdir", "--output_dir", help="Climo output directory", default=None)
    parser.add_argument("-m", "--model", help="Model name (eam or cam)", default="eam")
    parser.add_argument("-v", "--variable", help="Variable names", default=None)
    parser.add_argument("-t", "--time_freq", help="Time frequency (sea=seasonal | mon=monthly)", default=None)

    return parser.parse_args()


def main():
    """Main function to process climate data."""
    args = parse_arguments()

    output_dir = args.output_dir if args.output_dir is not None else args.input_dir

    start_time = time.perf_counter()

    climo_instance = get_climo(
        case=args.case,
        start=args.start,
        path=args.input_dir,
        outpath=output_dir,
        end=args.end,
        ts=args.time_freq,
        mod=args.model,
    )

    if args.variable is not None:
        climo_instance.variable = args.variable

    climo_instance.get_nc()

    end_time = time.perf_counter()
    print(f"\nFinished in {round(end_time - start_time, 2)} second(s)")


if __name__ == "__main__":
    main()

