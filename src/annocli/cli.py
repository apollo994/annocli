import argparse
import os
import sys

from .core.alias_helpers import rewrite_gff_seqids_from_assembly
from .core.summary_helpers import print_annotation_summary, build_tsv_report
from .core.requests import download_file, make_request


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
        "taxids",
        nargs="+",
        type=int,
        help="Taxonomy IDs, can be species or larger group",
    )
    download_parser.add_argument(
        "--mode",
        choices=["dw", "prev", "links"],
        default="dw",
        help="'dw' download, 'prev' preview, 'links' print links (default: dw)",
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
        "--fix_alias",
        action="store_true",
        help="Match sequence name with assembly (works only with --add_asm)",
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
        "summary", help="Get information about features and biotypes availble"
    )
    summary_parser.add_argument(
        "taxids",
        nargs="+",
        type=int,
        help="Taxonomy IDs, can be species or larger group",
    )
    summary_parser.add_argument(
        "--ref_only",
        action="store_true",
        help="Download only annotations of ref_only assemblies",
    )
    summary_parser.add_argument(
        "--tsv",
        help="Get annotation summary in tsv format",
    )

    args = parser.parse_args()

    request_params = {}

    if args.taxids:
        request_params["taxids"] = args.taxids
    if args.ref_only:
        request_params["refseq_categories"] = "reference genome"

    if args.command == "download":

        annotations_json = make_request("/annotations", params=request_params)

        assembly_dict = {}
        if args.add_asm:
            assemblies_json = make_request("/assemblies", params=request_params)
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

                source_filepath = None

                if source_url != "NA":
                    loc = -2 if source_url.endswith(".gz") else -1
                    ext = source_url.split(".")[loc:]
                    source_filename = f"{annotation_name}.{'.'.join(ext)}"
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
                                if args.fix_alias and source_filepath:

                                    if source_filepath.endswith(".gz"):
                                        extention = ".".join(
                                            source_filepath.split(".")[-2:]
                                        )

                                    else:
                                        extention = source_filepath.split(".")[-1]

                                    alias_fixed_filepath = source_filepath.replace(
                                        extention, f"aliasMatch.{extention}"
                                    )

                                    alias_report = (
                                        f"{alias_fixed_filepath}.aliasMappings.tsv"
                                    )

                                    alias_mapping = rewrite_gff_seqids_from_assembly(
                                        source_filepath,
                                        assembly_filepath,
                                        alias_fixed_filepath,
                                    )

                                    with open(alias_report, "w") as alias_report_out:
                                        for k, v in alias_mapping.items():
                                            alias_report_out.write(f"{k}\t{v}\n")

                                    print(
                                        f"Annotation matching assembly's aliases: {alias_fixed_filepath}",
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

    elif args.command == "alias":
        if args.output is None:

            loc = -2 if args.annotation.endswith(".gz") else -1
            extentions = args.annotation.split(".")
            extentions.insert(loc, "aliasMatch")
            args.output = ".".join(extentions)

        alias_mapping = rewrite_gff_seqids_from_assembly(
            args.annotation,
            args.assembly,
            args.output,
        )

        alias_report = f"{args.output}.aliasMappings.tsv"
        with open(alias_report, "w") as alias_report_out:
            for k, v in alias_mapping.items():
                alias_report_out.write(f"{k}\t{v}\n")

    elif args.command == "summary":

        annotations_json = make_request("/annotations", params=request_params)

        for i in annotations_json["results"]:

            print_annotation_summary(i)

            if args.tsv:
                biotype_json = make_request(
                    "/annotations/frequencies/biotype", params=request_params
                )
                feature_type_json = make_request(
                    "/annotations/frequencies/feature_type", params=request_params
                )
                feature_source_json = make_request(
                    "/annotations/frequencies/feature_source", params=request_params
                )

                build_tsv_report(args.tsv,
                                 annotations_json = annotations_json,
                                 biotype_json = biotype_json,
                                 feature_source_json = feature_source_json,
                                 feature_type_json = feature_type_json)

                # print(biotype_json)
                # print(feature_type_json)
                # print(feature_source_json)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
