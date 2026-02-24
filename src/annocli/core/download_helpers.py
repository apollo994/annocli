import os
import sys

from .alias_helpers import rewrite_gff_seqids_from_assembly
from .general_helpers import (get_extension_string, get_file_extension_parts,
                              insert_suffix_before_extension,
                              write_tsv_mapping)
from .requests import download_file, make_request


def fetch_annotations_and_assemblies(request_params, include_assemblies):
    """
    Fetch annotations and optionally assemblies from the API.

    Args:
        request_params: Dictionary of request parameters
        include_assemblies: Boolean indicating whether to fetch assemblies

    Returns:
        Tuple of (annotations_json, assembly_dict)
    """
    annotations_json = make_request("/annotations", params=request_params)

    assembly_dict = {}
    if include_assemblies:
        assemblies_json = make_request("/assemblies", params=request_params)
        assembly_dict = {
            asm["assembly_accession"]: asm for asm in assemblies_json.get("results", [])
        }

    return annotations_json, assembly_dict


def build_annotation_paths(result, output_dir):
    """
    Build file paths and names for annotation files.

    Args:
        result: Annotation result dictionary
        output_dir: Base output directory

    Returns:
        Dictionary with annotation_name, annotation_folder, organism_name, taxid, assembly_accession
    """
    annotation_id = result.get("annotation_id", "NA")
    organism_name = result.get("organism_name", "NA").replace(" ", "_")
    taxid = result.get("taxid", "NA")
    database = result.get("source_file_info", {}).get("database", "NA")
    assembly_accession = result.get("assembly_accession", "NA")

    annotation_name = "_".join(
        [organism_name, taxid, database, assembly_accession, annotation_id]
    )
    annotation_folder = os.path.join(
        output_dir, "_".join([organism_name, taxid]), assembly_accession
    )

    return {
        "annotation_name": annotation_name,
        "annotation_folder": annotation_folder,
        "organism_name": organism_name,
        "taxid": taxid,
        "assembly_accession": assembly_accession,
    }


def print_download_commands(
    annotation_folder,
    source_url,
    source_filepath,
    assembly_url=None,
    assembly_filepath=None,
):
    """
    Print wget commands for manual download (links mode).

    Args:
        annotation_folder: Directory path
        source_url: Annotation file URL
        source_filepath: Target annotation file path
        assembly_url: Optional assembly file URL
        assembly_filepath: Optional target assembly file path
    """
    print(f"mkdir -p {annotation_folder}")
    print(f"wget {source_url} -O {source_filepath}")

    if assembly_url and assembly_filepath:
        print(f"wget {assembly_url} -O {assembly_filepath}")


def download_annotation_file(source_url, source_filepath, annotation_folder):
    """
    Download annotation file to specified path.

    Args:
        source_url: URL to download from
        source_filepath: Target file path
        annotation_folder: Directory to create if needed

    Returns:
        Boolean indicating success
    """
    os.makedirs(annotation_folder, exist_ok=True)

    try:
        download_file(source_url, source_filepath)
        print(f"[INFO] Downloaded annotation to {source_filepath}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download annotation: {e}", file=sys.stderr)
        return False


def process_alias_fixing(source_filepath, assembly_filepath):
    """
    Process alias fixing between annotation and assembly files.

    Args:
        source_filepath: Path to annotation file
        assembly_filepath: Path to assembly file
    """
    extention = get_extension_string(source_filepath)
    alias_fixed_filepath = insert_suffix_before_extension(source_filepath, "aliasMatch")
    alias_report = f"{alias_fixed_filepath}.aliasMappings.tsv"

    alias_mapping = rewrite_gff_seqids_from_assembly(
        source_filepath,
        assembly_filepath,
        alias_fixed_filepath,
    )

    write_tsv_mapping(alias_mapping, alias_report)

    print(
        f"[INFO] Annotation matching assembly's aliases: {alias_fixed_filepath}",
        file=sys.stderr,
    )


def download_assembly_file(assembly_url, assembly_filepath, source_filepath, fix_alias):
    """
    Download assembly file and optionally fix aliases.

    Args:
        assembly_url: URL to download from
        assembly_filepath: Target file path
        source_filepath: Path to annotation file (for alias fixing)
        fix_alias: Boolean indicating whether to fix aliases

    Returns:
        Boolean indicating success
    """
    try:
        download_file(assembly_url, assembly_filepath)
        print(f"[INFO] Downloaded assembly to {assembly_filepath}", file=sys.stderr)

        if fix_alias and source_filepath:
            process_alias_fixing(source_filepath, assembly_filepath)

        return True
    except Exception as e:
        print(f"[ERROR] Failed to download assembly: {e}", file=sys.stderr)
        return False


def process_annotation_result(result, args, assembly_dict):
    """
    Process a single annotation result for download or link generation.

    Args:
        result: Annotation result dictionary
        args: Command-line arguments
        assembly_dict: Dictionary of assembly information
    """
    source_url = result.get("source_file_info", {}).get("url_path", "NA")

    paths = build_annotation_paths(result, args.output)
    annotation_folder = paths["annotation_folder"]
    annotation_name = paths["annotation_name"]
    assembly_accession = paths["assembly_accession"]

    source_filepath = None

    if source_url != "NA":
        ext = get_file_extension_parts(source_url)
        source_filename = f"{annotation_name}.{'.'.join(ext)}"
        source_filepath = os.path.join(annotation_folder, source_filename)

        if args.mode == "links":
            assembly_url = None
            assembly_filepath = None

            if args.add_asm:
                assembly_info = assembly_dict.get(assembly_accession, {})
                assembly_url = assembly_info.get("download_url", "NA")
                if assembly_url != "NA":
                    assembly_filename = assembly_url.split("/")[-1]
                    assembly_filepath = os.path.join(
                        annotation_folder, assembly_filename
                    )

            print_download_commands(
                annotation_folder,
                source_url,
                source_filepath,
                assembly_url if assembly_url != "NA" else None,
                assembly_filepath,
            )
        else:
            download_annotation_file(source_url, source_filepath, annotation_folder)

    if args.add_asm and args.mode != "links":
        assembly_info = assembly_dict.get(assembly_accession, {})
        assembly_url = assembly_info.get("download_url", "NA")

        if assembly_url != "NA":
            assembly_filename = assembly_url.split("/")[-1]
            assembly_filepath = os.path.join(annotation_folder, assembly_filename)
            download_assembly_file(
                assembly_url, assembly_filepath, source_filepath, args.fix_alias
            )


def print_preview(args, annotations_json):
    """
    Print preview information about the download operation.

    Args:
        args: Command-line arguments
        annotations_json: JSON response with annotation data
    """
    label_w = 20
    print(f"{'Taxids:':<{label_w}} {args.taxids}")
    print(f"{'Annotations:':<{label_w}} {len(annotations_json.get('results', []))}")
    print(f"{'Only reference:':<{label_w}} {args.ref_only}")
    print(f"{'Include assemblies:':<{label_w}} {args.add_asm}")


def handle_download_command(args, request_params):
    """
    Handle the download command logic.

    Args:
        args: Parsed command-line arguments
        request_params: Dictionary of request parameters
    """
    
    if args.fix_alias and not args.add_asm:
        print("[ERROR] --fix-alias requires --add-asm", file=sys.stderr)
        return

    annotations_json, assembly_dict = fetch_annotations_and_assemblies(
        request_params, args.add_asm
    )

    if args.mode in ["dw", "links"]:
        if args.mode == "dw":
            os.makedirs(args.output, exist_ok=True)

        for result in annotations_json.get("results", []):
            process_annotation_result(result, args, assembly_dict)

    elif args.mode == "prev":
        print_preview(args, annotations_json)


