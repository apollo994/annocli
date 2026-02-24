"""
General utility functions shared across multiple modules.

This module contains common helper functions extracted from various
helper modules to avoid code duplication and improve maintainability.
"""


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


def validate_taxids(taxids):
    """
    Query each taxid individually and report how many annotation entries were found.

    Prints an [INFO] message per taxid with the number of annotations found.
    Taxids with zero results are warned about and excluded from the returned list.

    Args:
        taxids: List of integer taxids to validate

    Returns:
        List of taxids (int) for which at least one annotation exists
    """
    import sys
    from .requests import core_request

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
