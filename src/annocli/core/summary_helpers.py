import csv
from textwrap import indent

from .requests import make_request


def handle_summary_command(args, request_params):
    """
    Handle the summary command logic.

    Args:
        args: Parsed command-line arguments
        request_params: Dictionary of request parameters
    """
    annotations_json = make_request("/annotations", params=request_params)

    for annotation in annotations_json["results"]:
        print_annotation_summary(annotation)

    if args.tsv:
        fetch_and_build_summary_report(args.tsv, request_params, annotations_json)


def fetch_and_build_summary_report(output_file, request_params, annotations_json):
    """
    Fetch frequency data and build summary report.

    Args:
        output_file: Path to output TSV file
        request_params: Dictionary of request parameters
        annotations_json: Already-fetched annotations data
    """
    biotype_json = make_request(
        "/annotations/frequencies/biotype", params=request_params
    )
    feature_type_json = make_request(
        "/annotations/frequencies/feature_type", params=request_params
    )
    feature_source_json = make_request(
        "/annotations/frequencies/feature_source", params=request_params
    )

    build_summary_report(
        output_file,
        annotations_json=annotations_json,
        biotype_json=biotype_json,
        feature_source_json=feature_source_json,
        feature_type_json=feature_type_json,
    )


def make_summary_label(group: str, values):
    """
    build the label to use in the summary table
    """
    return [f"has_{group}.{v}" for v in values]


def build_summary_report(
    out_file,
    annotations_json={},
    biotype_json={},
    feature_source_json={},
    feature_type_json={},
):
    """
    Build a unified summary tsv where the set of all possible features are columns
    and the value is 1 or 0 depending if it's present. For the other information
    in the summary take inspiration from the print annotaion function below
    """

    # Prepare header row
    header = [
        "annotation_id",
        "organism_name",
        "taxid",
        "assembly_accession",
        "assembly_name",
        "database",
        "url_path",
        "release_date",
        "has_biotype",
        "has_cds",
        "has_exon",
    ]

    ft_names = ["biotypes", "sources", "types"]
    ft_jsons = [biotype_json, feature_source_json, feature_type_json]
    bool_ft_list = []
    for group, values in zip(ft_names, ft_jsons):
        bool_ft_list.extend(make_summary_label(group, values))
    header.extend(bool_ft_list)

    # Process each annotation
    rows = []

    for annotation in annotations_json["results"]:
        src = annotation.get("source_file_info", {}) or {}
        feats = annotation.get("features_summary", {}) or {}

        # Build basic info row
        row = [
            annotation.get("annotation_id", ""),
            annotation.get("organism_name", ""),
            annotation.get("taxid", ""),
            annotation.get("assembly_accession", ""),
            annotation.get("assembly_name", ""),
            src.get("database", ""),
            src.get("url_path", ""),
            src.get("release_date", ""),
            feats.get("has_biotype", ""),
            feats.get("has_cds", ""),
            feats.get("has_exon", ""),
        ]

        # Add feature presence columns (True or False)
        for feature in bool_ft_list:
            ft_class = feature.split(".")[0].split("_")[1]  # eg. biotype
            ft_name = feature.split(f"{ft_class}.")[1]  # eg. sRNA, protein_coding
            ft_list = feats.get(ft_class, [])
            if ft_name in ft_list:
                ft_val = True
            else:
                ft_val = False
            row.append(ft_val)

        rows.append(row)

    # Write TSV file
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)


def print_annotation_summary(d: dict) -> None:
    src = d.get("source_file_info", {}) or {}
    feats = d.get("features_summary", {}) or {}

    # small helpers
    def line(k, v):
        return f"{k:<18}: {v}"

    def join_list(xs, n=8):
        xs = list(xs or [])
        if len(xs) <= n:
            return ", ".join(map(str, xs))
        return ", ".join(map(str, xs[:n])) + f", … (+{len(xs)-n} more)"

    annotation_id = d.get("annotation_id")
    print("-" * 60)
    print(f"Annotation summary (ID: {annotation_id})")
    print("-" * 60)
    print(line("Organism", d.get("organism_name")))
    print(line("TaxID", d.get("taxid")))
    print(
        line("Assembly", f"{d.get('assembly_accession')}  ({d.get('assembly_name')})")
    )
    print(line("Database", src.get("database")))
    print(line("URL", src.get("url_path")))
    print(line("Release date", src.get("release_date")))
    print(line("Has biotype", feats.get("has_biotype")))
    print(line("Has CDS", feats.get("has_cds")))
    print(line("Has exon", feats.get("has_exon")))
    print(line("Types", join_list(feats.get("types"), n=25)))
    print(line("Sources", join_list(feats.get("sources"), n=25)))
    print(line("Biotypes", join_list(feats.get("biotypes"), n=25)))
    print(line("Missing ID", join_list(feats.get("types_missing_id"), n=25)))

    rtc = feats.get("root_type_counts", {}) or {}
    if rtc:
        print()
        print("Root type counts (features with no children)")
        print(indent("\n".join(f"- {k}: {v}" for k, v in rtc.items()), "  "))
        print("-" * 60)
