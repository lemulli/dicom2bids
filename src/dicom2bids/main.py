# main.py
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="DICOM to BIDS pipeline CLI",
        epilog="Example usage:\n"
               "  dicom2bids convert-and-organize /path/to/subjects /path/to/BIDS\n"
               "  dicom2bids metadata-enrichment /path/to/input.csv /path/to/old_bids /path/to/new_bids /path/to/t2_json_map\n"
               "  dicom2bids finalize-pipeline /path/to/BIDS /path/to/metadata.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    # Subcommand: convert-and-organize
    parser_convert = subparsers.add_parser("convert-and-organize", help="Convert DICOMs to NIfTI and create partial BIDS")
    parser_convert.add_argument("input_dir", help="Path to the original DICOM folder(s)")
    parser_convert.add_argument("output_dir", help="Path to the new BIDS folder")
    
    # Subcommand: metadata-enrichment
    parser_meta = subparsers.add_parser("metadata-enrichment", help="Expand CSV, copy NIfTIs, read headers with nibabel")
    parser_meta.add_argument("input_csv", help="Original or partially filled CSV with subject/scan info")
    parser_meta.add_argument("old_bids_dir", help="Path to the original BIDS folder containing NIfTIs")
    parser_meta.add_argument("new_bids_dir", help="Path to the new BIDS folder for copied files")
    parser_meta.add_argument("t2_json_map", help="Path to T2 JSON mapping file")

    # Subcommand: finalize-pipeline
    parser_final = subparsers.add_parser("finalize-pipeline", help="Check JSONs, remove them, zip DWI, etc.")
    parser_final.add_argument("bids_dir", help="Path to the BIDS folder")
    parser_final.add_argument("csv_path", help="CSV metadata file to update with final references")

    # Parse CLI
    args = parser.parse_args()

    if args.command == "convert-and-organize":
        from .convert_and_organize import main as convert_main
        convert_main(args.input_dir, args.output_dir)

    elif args.command == "metadata-enrichment":
        from .metadata_enrichment import main as meta_main
        meta_main(args.input_csv, args.old_bids_dir, args.new_bids_dir, args.t2_json_map)

    elif args.command == "finalize-pipeline":
        from .finalize_pipeline import main as finalize_main
        finalize_main(args.bids_dir, args.csv_path)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()