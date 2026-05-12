"""Command-line interface for laion-fmri."""

import argparse
import sys


_FILTER_ENTITIES = (
    ("ses", "BIDS session ID, e.g. ses-01 or 'averages'"),
    ("task", "BIDS task entity, e.g. images"),
    ("space", "BIDS space entity, e.g. T1w"),
    ("desc", "BIDS desc entity, e.g. singletrial"),
    ("stat", "BIDS stat entity, e.g. effect"),
    ("suffix", "BIDS suffix, e.g. statmap or events"),
    ("extension", "File extension, e.g. nii.gz or tsv"),
)


def main(argv=None):
    """Entry point for the laion-fmri CLI."""
    parser = argparse.ArgumentParser(
        prog="laion-fmri",
        description="LAION-fMRI dataset management tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    config_parser = subparsers.add_parser(
        "config", help="Configure the data directory"
    )
    config_parser.add_argument(
        "--data-dir", required=True,
        help="Path to the data directory",
    )

    download_parser = subparsers.add_parser(
        "download", help="Download fMRI files for a subject"
    )
    download_parser.add_argument(
        "--subject", required=True,
        help="Subject ID (e.g., sub-01) or 'all'",
    )
    for entity, description in _FILTER_ENTITIES:
        download_parser.add_argument(
            f"--{entity}", nargs="+", default=None,
            help=f"{description} (one or more values).",
        )
    download_parser.add_argument(
        "--n-jobs", type=int, default=1,
        help="Number of parallel `aws s3 cp` workers (default: 1).",
    )
    download_parser.add_argument(
        "--include-stimuli", action="store_true",
        help=(
            "Include the stimuli. First call walks "
            "through a Data Use Agreement form; subsequent calls "
            "reuse the cached request_id."
        ),
    )
    download_parser.add_argument(
        "--include-embeddings", nargs="*", default=None, metavar="MODEL",
        help=(
            "Include stimulus embeddings. Pass with no value for "
            "all models, or one or more labels (e.g. CLIP DINOv2)."
        ),
    )

    info_parser = subparsers.add_parser(
        "info", help="Show dataset information"
    )
    info_parser.add_argument(
        "--subject", default=None,
        help="Show info for a specific subject",
    )

    subparsers.add_parser(
        "download-stimuli",
        help=(
            "Download the stimuli (dataset-wide, "
            "subject-independent). First call walks through the Data "
            "Use Agreement; subsequent calls reuse the cached "
            "request_id."
        ),
    )

    embeddings_parser = subparsers.add_parser(
        "download-embeddings",
        help=(
            "Download stimulus embeddings (public, no DUA). "
            "Default downloads all four model files."
        ),
    )
    embeddings_parser.add_argument(
        "--model", nargs="+", default=None, metavar="MODEL",
        help="Subset of models to fetch (e.g. CLIP DINOv2).",
    )
    embeddings_parser.add_argument(
        "--n-jobs", type=int, default=1,
        help="Number of parallel `aws s3 cp` workers (default: 1).",
    )

    subparsers.add_parser(
        "download-segmentations",
        help=(
            "Download per-stimulus object-segmentation masks "
            "(public, no DUA, ~68 MB)."
        ),
    )

    subparsers.add_parser(
        "download-captions",
        help="Download per-stimulus captions (public, no DUA).",
    )

    subparsers.add_parser(
        "request-access",
        help=(
            "Walk through the LAION-fMRI Data Use Agreement form and "
            "cache the resulting request_id. Run once per machine."
        ),
    )

    login_parser = subparsers.add_parser(
        "login",
        help="Cache an existing request_id (e.g. obtained from the web form).",
    )
    login_parser.add_argument(
        "--request-id", required=True,
        help="Raw request_id (the lfm_… string shown by the web form).",
    )

    subparsers.add_parser(
        "logout",
        help="Remove the cached request_id from this machine.",
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
    elif args.command == "download-stimuli":
        _handle_download_stimuli(args)
    elif args.command == "download-embeddings":
        _handle_download_embeddings(args)
    elif args.command == "download-segmentations":
        _handle_download_segmentations(args)
    elif args.command == "download-captions":
        _handle_download_captions(args)
    elif args.command == "request-access":
        _handle_request_access(args)
    elif args.command == "login":
        _handle_login(args)
    elif args.command == "logout":
        _handle_logout(args)


def _handle_config(args):
    """Handle the config subcommand."""
    from laion_fmri.config import dataset_initialize
    dataset_initialize(args.data_dir)
    print(f"Data directory set to: {args.data_dir}")


def _handle_download(args):
    """Handle the download subcommand."""
    from laion_fmri.download import download
    if args.include_embeddings is None:
        include_embeddings = False
    elif args.include_embeddings == []:
        include_embeddings = True
    else:
        include_embeddings = args.include_embeddings
    download(
        subject=args.subject,
        ses=args.ses,
        task=args.task,
        space=args.space,
        desc=args.desc,
        stat=args.stat,
        suffix=args.suffix,
        extension=args.extension,
        n_jobs=args.n_jobs,
        include_stimuli=args.include_stimuli,
        include_embeddings=include_embeddings,
    )


def _handle_info(args):
    """Handle the info subcommand."""
    from laion_fmri.discovery import describe
    describe()


def _handle_download_stimuli(args):
    """Handle the download-stimuli subcommand (stimuli only, no fMRI)."""
    from laion_fmri.download import download_stimuli
    download_stimuli()


def _handle_download_embeddings(args):
    """Handle the download-embeddings subcommand."""
    from laion_fmri.download import download_embeddings
    models = args.model if args.model else "all"
    download_embeddings(models=models, n_jobs=args.n_jobs)


def _handle_download_segmentations(args):
    """Handle the download-segmentations subcommand."""
    from laion_fmri.download import download_segmentations
    download_segmentations()


def _handle_download_captions(args):
    """Handle the download-captions subcommand."""
    from laion_fmri.download import download_captions
    download_captions()


def _handle_request_access(args):
    """Walk the user through the Data Use Agreement form."""
    from laion_fmri.download import request_stimulus_access
    request_stimulus_access()


def _handle_login(args):
    """Cache an existing request_id."""
    from laion_fmri._stimulus_access import (
        ACCESS_SERVICE_URL,
        AccessNotFoundError,
        AccessServiceError,
        refresh_urls,
        save_request_id,
    )
    raw = args.request_id.strip()
    # Sanity-check by hitting /refresh; if it works the id is valid.
    try:
        refresh_urls(raw)
    except AccessNotFoundError:
        print(f"Server doesn't know that request_id. Did you mistype it?", file=sys.stderr)
        sys.exit(1)
    except AccessServiceError as exc:
        print(f"Could not validate request_id: {exc}", file=sys.stderr)
        sys.exit(1)
    saved_path = save_request_id(raw, server_url=ACCESS_SERVICE_URL)
    print(f"✓ request_id saved to {saved_path}")


def _handle_logout(args):
    """Clear the cached request_id."""
    from laion_fmri._stimulus_access import clear_request_id
    if clear_request_id():
        print("✓ cached request_id removed.")
    else:
        print("No cached request_id to remove.")


if __name__ == "__main__":
    sys.exit(main())
