import argparse
from .step00_convert_and_sort import run_step00
from .step01_constants_to_csv import run_step01
# ... import others

def main():
    parser = argparse.ArgumentParser(description="DICOM-to-BIDS Conversion Pipeline")
    parser.add_argument("step", type=str, help="Which step to run (00, 01, 02, 03, 04, 05, or all).")
    parser.add_argument("--momma_dir", type=str, default="/path/to/default", help="Path to input directory.")
    args = parser.parse_args()

    if args.step == "00":
        run_step00(args.momma_dir)
    elif args.step == "01":
        run_step01(args.momma_dir)
    # ...
    elif args.step == "all":
        run_step00(args.momma_dir)
        run_step01(args.momma_dir)
        # ...
    else:
        print("Invalid step specified.")

if __name__ == "__main__":
    main()