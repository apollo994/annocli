import argparse
import os
import sys

from .core.helpers import rewrite_gff_seqids_from_assembly
from .core.requests import (download_file, get_annotations, get_assemblies,
                            get_filename_from_url)


def main():
    parser = argparse.ArgumentParser(
        description="annocli: command-line tool to query and download genome annotations"
    )
    parser.add_argument("--version", action="version", version="annocli 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    download_parser = subparsers.add_parser(
        "download", help="Download annotations for given taxids"
    )
    download_parser.add_argument(
        "taxids",
        nargs="+",
        type=int,
        help="Taxonomy IDs, can be species or larger group",
    )
    download_parser.add_argument(
        "--ref_only",
        action="store_true",
        help="Download only annotations of ref_only assemblies",
    )
    download_parser.add_argument(
        "--add_asm", action="store_true", help="Download also assemblies"
    )
    download_parser.add_argument(
        "--mode",
        choices=["dw", "prev", "links"],
        default="dw",
        help="'dw' download, 'prev' preview, 'links' print links (default: dw)",
    )
    download_parser.add_argument(
        "--preview", action="store_true", help="Only print number of annotations"
    )
    download_parser.add_argument(
        "--links", action="store_true", help="Only print wget commands"
    )
    download_parser.add_argument(
        "--limit", type=int, default=0, help="Limit number of results"
    )
    download_parser.add_argument(
        "--offset", type=int, default=0, help="Offset for results"
    )
    download_parser.add_argument(
        "-o",
        "--output",
        default="annotation_downloads",
        help="Folder to save annotations",
    )

    # Alias command
    alias_parser = subparsers.add_parser(
        "alias", help="Match alias between annotation and assembly"
    )
    alias_parser.add_argument(
        "annotation",
        help="Path to the annotation GFF file"
    )
    alias_parser.add_argument(
        "assembly",
        help="Path to the assembly FASTA file"
    )
    alias_parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for updated annotation file"
    )



    args = parser.parse_args()

    if args.command == "download":

        annotations_json = get_annotations(
            taxids=args.taxids,
            limit=args.limit,
            offset=args.offset,
            ref_only=args.ref_only,
        )

        assembly_dict = {}
        if args.add_asm:
            assemblies_json = get_assemblies(
                taxids=args.taxids,
                limit=args.limit,
                offset=args.offset,
                ref_only=args.ref_only,
            )
            assembly_dict = {
                asm["assembly_accession"]: asm
                for asm in assemblies_json.get("results", [])
            }

        ### Download or Links
        if args.mode in ["dw", "links"]:

            if args.mode == "dw":
                os.makedirs(args.output, exist_ok=True)

            for result in annotations_json.get("results", []):

                annotation_id = result.get("annotation_id", "NA")
                organism_name = result.get("organism_name", "NA").replace(" ", "_")
                taxid = result.get("taxid", "NA")
                source_url = result.get("source_file_info", {}).get("url_path", "NA")
                database = result.get("source_file_info", {}).get("database", "NA")
                assembly_accession = result.get("assembly_accession", "NA")

                annotation_name = "_".join(
                    [organism_name, taxid, database, assembly_accession, annotation_id]
                )
                annotation_folder = os.path.join(
                    args.output, "_".join([organism_name, taxid]), assembly_accession
                )

                if source_url != "NA":
                    source_filename = get_filename_from_url(source_url, annotation_name)
                    source_filepath = os.path.join(annotation_folder, source_filename)

                    if args.mode == "links":
                        print(f"mkdir -p {annotation_folder}")
                        print(f"wget {source_url} -O {source_filepath}")

                    else:
                        os.makedirs(annotation_folder, exist_ok=True)

                        try:
                            download_file(source_url, source_filepath)
                            print(
                                f"Downloaded annotation to {source_filepath}",
                                file=sys.stderr,
                            )
                        except Exception as e:
                            print(
                                f"Failed to download annotation: {e}", file=sys.stderr
             )

            if args.add_asm:
                    assembly_info = assembly_dict.get(assembly_accession, {})
                    assembly_url = assembly_info.get("download_url", "NA")

                    # Download assembly file
                    if assembly_url != "NA":
                        assembly_filename = assembly_url.split("/")[-1]
                        assembly_filepath = os.path.join(
                            annotation_folder, assembly_filename
                        )
                        if args.mode == "links":
                            print(f"wget {assembly_url} -O {assembly_filepath}")

                        else:
                            try:
                                download_file(assembly_url, assembly_filepath)
                                print(
                                    f"Downloaded assembly to {assembly_filepath}",
                                    file=sys.stderr,
                                )
                            except Exception as e:
                                print(
                                    f"Failed to download assembly: {e}", file=sys.stderr
                                )



        ### Preview
        elif args.mode == "prev":
            label_w = 20
            print(f"{'Taxids:':<{label_w}} {args.taxids}")
            print(
                f"{'Annotations:':<{label_w}} {len(annotations_json.get('results', []))}"
            )
            print(f"{'Only reference:':<{label_w}} {args.ref_only}")
            print(f"{'Include assemblies:':<{label_w}} {args.add_asm}")
    
    elif args.command == 'alias':
        if args.output is None:

            loc = -2 if args.annotation.endswith(".gz") else -1
            extentions = args.annotation.split('.')
            extentions.insert(loc, "aliasMatch")
            args.output = ".".join(extentions)

        alias_mapping = rewrite_gff_seqids_from_assembly(
            args.annotation,
            args.assembly,
            args.output,
        )
        print(alias_mapping)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
