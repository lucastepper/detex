import argparse
from .detex import detex, generate_detexed_pdf, convert_detexed_pdf_to_txt


def main():
    """Main function to execute all the different detex functions."""
    parser = argparse.ArgumentParser(description="Detex")
    parser.add_argument(
        "mode",
        choices=["detex"],
        help="Mode to execute",
    )
    parser.add_argument(
        "file",
        type=str,
        help="File to detex",
    )
    args = parser.parse_args()

    if args.mode == "detex":
        detex(args.file)
        generate_detexed_pdf()
        convert_detexed_pdf_to_txt()
    else:
        parser.error("Mode not provided. Please specify a mode to execute as first argument.")
