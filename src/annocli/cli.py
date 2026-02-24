import argparse
import sys

from .core.alias_helpers import handle_alias_command
from .core.download_helpers import handle_download_command
from .core.general_helpers import resolve_input_ids, validate_taxids, validate_annotation_ids
from .core.stats_helpers import handle_stats_command
from .core.summary_helpers import handle_summary_command


def main():
    parser = argparse.ArgumentParser(
        description="annocli: command-line tool to query and download genome annotations"
    )
    parser.add_argument("--version", action="version", version="annocli 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ##### Download command
    download_parser = subparsers.add_parser(
        "download", help="Download annotations for given taxids"
    )
    download_parser.add_argument(
        "--taxids",
        nargs="+",
        help="Taxonomy IDs, can be species or larger group",
    )
    download_parser.add_argument(
        "--taxids-file",
        help="Path to file with taxonomy IDs, one per line",
    )
    download_parser.add_argument(
        "--annotation-ids",
        nargs="+",
        help="Annotation ID from Annotrieve (md5 checksum)",
    )
    download_parser.add_argument(
        "--annotation-ids-file",
        help="Path to file with annotation IDs from Annotrieve, one per line",
    )
    download_parser.add_argument(
        "--mode",
        choices=["dw", "prev", "links"],
        default="dw",
        help="'dw' download, 'prev' preview, 'links' print links (default: dw)",
    )
    download_parser.add_argument(
        "--ref-only",
        action="store_true",
        help="Download only annotations of reference assemblies",
    )
    download_parser.add_argument(
        "--add-asm", action="store_true", help="Download also assemblies"
    )
    download_parser.add_argument(
        "--fix-alias",
        action="store_true",
        help="Match sequence name with assembly (works only with --add-asm)",
    )
    download_parser.add_argument(
        "-o",
        "--output",
        default="annotation_downloads",
        help="Folder to save annotations",
    )

    ##### Alias command
    alias_parser = subparsers.add_parser(
        "alias", help="Match alias between annotation and assembly"
    )
    alias_parser.add_argument("annotation", help="Path to the annotation GFF file")
    alias_parser.add_argument("assembly", help="Path to the assembly FASTA file")
    alias_parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for updated annotation file",
    )

    ##### Summary command
    summary_parser = subparsers.add_parser(
        "summary", help="Get information about features and biotypes available"
    )
    summary_parser.add_argument(
        "--taxids",
        nargs="+",
        help="Taxonomy IDs, can be species or larger group",
    )
    summary_parser.add_argument(
        "--taxids-file",
        help="Path to file with taxonomy IDs, one per line",
    )
    summary_parser.add_argument(
        "--annotation-ids",
        nargs="+",
        help="Annotation ID from Annotrieve (md5 checksum)",
    )
    summary_parser.add_argument(
        "--annotation-ids-file",
        help="Path to file with annotation IDs from Annotrieve, one per line",
    )
    summary_parser.add_argument(
        "--ref-only",
        action="store_true",
        help="Consider only annotations of reference assemblies",
    )
    summary_parser.add_argument(
        "--tsv",
        help="File to save annotation summary in tsv format",
    )

    ##### Stats command
    stats_parser = subparsers.add_parser("stats", help="Get summary statistics")
    stats_parser.add_argument(
        "--taxids",
        nargs="+",
        help="Taxonomy IDs, can be species or larger group",
    )
    stats_parser.add_argument(
        "--taxids-file",
        help="Path to file with taxonomy IDs, one per line",
    )
    stats_parser.add_argument(
        "--annotation-ids",
        nargs="+",
        help="Annotation ID from Annotrieve (md5 checksum)",
    )
    stats_parser.add_argument(
        "--annotation-ids-file",
        help="Path to file with annotation IDs from Annotrieve, one per line",
    )
    stats_parser.add_argument(
        "--ref-only",
        action="store_true",
        help="Consider only annotations of reference assemblies",
    )
    stats_parser.add_argument(
        "--tsv",
        help="File to save annotation summary in tsv format",
    )

    # build arg parser
    args = parser.parse_args()

    ######
    
    # Build API request parameters

    REQUEST_LIMIT = 1000
 
    request_params = {
        "limit": REQUEST_LIMIT,
        **({"refseq_categories": "reference genome"} if hasattr(args, 'ref_only') and args.ref_only else {}),
    }

    if args.command in ("download", "summary", "stats"):
        input_mode, ids = resolve_input_ids(args)
        if input_mode == "taxids":
            valid_ids = validate_taxids(ids)
            request_params["taxids"] = ",".join(valid_ids)
        else:
            valid_ids = validate_annotation_ids(ids)
            request_params["md5_checksums"] = ",".join(valid_ids)

    #####

    # Execute desired command

    if args.command == "download":
        handle_download_command(args, request_params)

    elif args.command == "alias":
        handle_alias_command(args)

    elif args.command == "summary":
        handle_summary_command(args, request_params)

    elif args.command == "stats":
        handle_stats_command(args, request_params)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
