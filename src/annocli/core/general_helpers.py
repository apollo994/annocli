"""
General utility functions shared across multiple modules.

This module contains common helper functions extracted from various
helper modules to avoid code duplication and improve maintainability.
"""

import sys
from .requests import core_request

def get_file_extension_parts(filepath):
    """
    Extract file extension from filepath, handling compressed files.

    For compressed files (.gz), returns last 2 parts, otherwise last part.

    Args:
        filepath: File path or URL string

    Returns:
        List of extension parts (e.g., ['gff3', 'gz'] or ['gff3'])

    Examples:
        >>> get_file_extension_parts("file.gff3.gz")
        ['gff3', 'gz']
        >>> get_file_extension_parts("file.gff3")
        ['gff3']
        >>> get_file_extension_parts("http://example.com/data.fna.gz")
        ['fna', 'gz']
    """
    loc = -2 if filepath.endswith(".gz") else -1
    return filepath.split(".")[loc:]


def get_extension_string(filepath):
    """
    Get file extension as a string, handling compressed files.

    Args:
        filepath: File path or URL string

    Returns:
        Extension string (e.g., 'gff3.gz' or 'gff3')

    Examples:
        >>> get_extension_string("file.gff3.gz")
        'gff3.gz'
        >>> get_extension_string("file.gff3")
        'gff3'
        >>> get_extension_string("/path/to/annotation.gtf.gz")
        'gtf.gz'
    """
    if filepath.endswith(".gz"):
        return ".".join(filepath.split(".")[-2:])
    else:
        return filepath.split(".")[-1]


def write_tsv_mapping(mapping_dict, output_path):
    """
    Write a dictionary to a TSV file (key-value pairs).

    Each line contains: key<TAB>value

    Args:
        mapping_dict: Dictionary to write (key-value pairs)
        output_path: Path to output TSV file

    Example:
        >>> mapping = {"chr1": "NC_000001", "chr2": "NC_000002"}
        >>> write_tsv_mapping(mapping, "mapping.tsv")
        # Creates file with:
        # chr1\tNC_000001
        # chr2\tNC_000002
    """
    with open(output_path, "w") as f:
        for key, value in mapping_dict.items():
            f.write(f"{key}\t{value}\n")


def insert_suffix_before_extension(filepath, suffix):
    """
    Insert a suffix before the file extension(s), handling compressed files.

    For compressed files (.gz), the suffix is inserted before both extension parts.
    For regular files, the suffix is inserted before the extension.

    Args:
        filepath: Original file path
        suffix: Suffix to insert (without dots)

    Returns:
        Modified filepath with suffix inserted

    Examples:
        >>> insert_suffix_before_extension("file.gff3.gz", "aliasMatch")
        'file.aliasMatch.gff3.gz'
        >>> insert_suffix_before_extension("file.gff3", "filtered")
        'file.filtered.gff3'
        >>> insert_suffix_before_extension("/path/data.fna.gz", "processed")
        '/path/data.processed.fna.gz'
    """
    loc = -2 if filepath.endswith(".gz") else -1
    extensions = filepath.split(".")
    extensions.insert(loc, suffix)
    return ".".join(extensions)


def get_nested_dict_value(dictionary, path, default="NA"):
    """
    Safely retrieve a nested dictionary value using dot notation path.

    Traverses nested dictionaries using a dot-separated path string.
    Returns default value if path doesn't exist or value is None.

    Args:
        dictionary: Dictionary to query
        path: Dot-separated path string (e.g., "features.biotype.count")
        default: Default value if path not found or value is None

    Returns:
        Value at path or default if not found

    Examples:
        >>> d = {"a": {"b": {"c": 42}}}
        >>> get_nested_dict_value(d, "a.b.c")
        42
        >>> get_nested_dict_value(d, "a.b.x", default="N/A")
        'N/A'
        >>> get_nested_dict_value(d, "a.missing.path")
        'NA'
        >>> data = {"stats": {"min": 10, "max": None}}
        >>> get_nested_dict_value(data, "stats.max", default=0)
        0
    """
    current = dictionary
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return default if current is None else current


def extract_nested_values(dictionary, paths, default="NA"):
    """
    Extract multiple nested values from a dictionary using path list.

    Convenience function to extract multiple values at once.
    Each path is processed using get_nested_dict_value().

    Args:
        dictionary: Dictionary to query
        paths: List of dot-separated path strings
        default: Default value for missing paths

    Returns:
        List of extracted values (in same order as paths)

    Examples:
        >>> d = {"stats": {"min": 10, "max": 100, "mean": 55}}
        >>> extract_nested_values(d, ["stats.min", "stats.max", "stats.median"])
        [10, 100, 'NA']
        >>> extract_nested_values(d, ["stats.min", "stats.mean"], default=0)
        [10, 55]
    """
    return [get_nested_dict_value(dictionary, path, default) for path in paths]


def read_ids_from_file(filepath):
    """
    Read IDs from a plain-text file, one entry per line.

    Args:
        filepath: Path to the file

    Returns:
        List of non-empty stripped strings
    """
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip()]


def resolve_input_ids(args):
    """
    Resolve and validate input IDs from all provided sources.

    Taxid sources (--taxids + --taxids-file) and annotation ID sources
    (--annotation-ids + --annotation-ids-file) are mutually exclusive.
    At least one source must be provided.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (mode, ids) where mode is "taxids" or "annotation_ids"
        and ids is a deduplicated list of taxids or annotation_ids

    Raises:
        SystemExit: If no inputs provided or both modes used simultaneously
    """

    taxids = list(getattr(args, "taxids", None) or [])
    if getattr(args, "taxids_file", None):
        taxids += read_ids_from_file(args.taxids_file)

    annotation_ids = list(getattr(args, "annotation_ids", None) or [])
    if getattr(args, "annotation_ids_file", None):
        annotation_ids += read_ids_from_file(args.annotation_ids_file)

    if taxids and annotation_ids:
        print(
            "[ERROR] --taxids/--taxids-file and --annotation-ids/--annotation-ids-file "
            "are mutually exclusive. Provide only one input mode.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not taxids and not annotation_ids:
        print(
            "[ERROR] No input provided. Supply --taxids, --taxids-file, "
            "--annotation-ids, or --annotation-ids-file.",
            file=sys.stderr,
        )
        sys.exit(1)

    if taxids:
        return ("taxids", list(dict.fromkeys(taxids)))
    return ("annotation_ids", list(dict.fromkeys(annotation_ids)))

def validate_annotation_ids(annotation_ids):
    """
    Query each annotation id individually and report if found or not.

    Args:
        annotation_ids: List of annotation id taxids to validate

    Returns:
        List of annotation ids found
    """
    import sys

    valid = []
    for id in annotation_ids:
        response = core_request("/annotations", params={"limit": 1, "md5_checksums": id})
        total = response.get("total", 0)
        if total == 0:
            print(f"[WARNING] annotation id {id}: no annotations found, skipping", file=sys.stderr)
        else:
            print(f"[INFO] annotation id {id}: found", file=sys.stderr)
            valid.append(id)
    return valid

def validate_taxids(taxids):
    """
    Query each taxid individually and report how many annotation entries were found.

    Prints an [INFO] message per taxid with the number of annotations found.
    Taxids with zero results are warned about and excluded from the returned list.

    Args:
        taxids: List of taxids to validate

    Returns:
        List of taxids for which at least one annotation exists
    """

    valid = []
    for taxid in taxids:
        response = core_request("/annotations", params={"limit": 1, "taxids": taxid})
        total = response.get("total", 0)
        if total == 0:
            print(f"[WARNING] taxid {taxid}: no annotations found, skipping", file=sys.stderr)
        else:
            print(f"[INFO] taxid {taxid}: {total} annotation(s) found", file=sys.stderr)
            valid.append(taxid)
    return valid
