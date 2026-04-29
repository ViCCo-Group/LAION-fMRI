"""Command-line interface for laion-fmri."""

import argparse
import sys


def main(argv=None):
    """Entry point for the laion-fmri CLI."""
    parser = argparse.ArgumentParser(
        prog="laion-fmri",
        description="LAION-fMRI dataset management tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    # config subcommand
    config_parser = subparsers.add_parser(
        "config", help="Configure the data directory"
    )
    config_parser.add_argument(
        "--data-dir", required=True,
        help="Path to the data directory",
    )

    # download subcommand
    download_parser = subparsers.add_parser(
        "download", help="Download dataset files"
    )
    download_parser.add_argument(
        "--subject", required=True,
        help="Subject ID (e.g., sub-01) or 'all'",
    )
    download_parser.add_argument(
        "--include-stimuli", action="store_true",
        help="Include stimulus images (requires ToU acceptance)",
    )

    # info subcommand
    info_parser = subparsers.add_parser(
        "info", help="Show dataset information"
    )
    info_parser.add_argument(
        "--subject", default=None,
        help="Show info for a specific subject",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return

    if args.command == "config":
        _handle_config(args)
    elif args.command == "download":
        _handle_download(args)
    elif args.command == "info":
        _handle_info(args)


def _handle_config(args):
    """Handle the config subcommand."""
    from laion_fmri.config import dataset_initialize
    dataset_initialize(args.data_dir)
    print(f"Data directory set to: {args.data_dir}")


def _handle_download(args):
    """Handle the download subcommand."""
    from laion_fmri.download import download
    download(
        subject=args.subject,
        include_stimuli=args.include_stimuli,
    )


def _handle_info(args):
    """Handle the info subcommand."""
    from laion_fmri.discovery import describe
    describe()


if __name__ == "__main__":
    sys.exit(main())
