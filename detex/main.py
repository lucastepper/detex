import argparse
from .detex import detex


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
    else:
        parser.error("Mode not provided. Please specify a mode to execute as first argument.")
