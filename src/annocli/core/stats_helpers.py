import csv
from textwrap import indent
from typing import Any, Mapping, Optional

from .general_helpers import extract_nested_values
from .requests import make_request


def handle_stats_command(args, request_params):
    """
    Handle the stats command logic.

    Args:
        args: Parsed command-line arguments
        request_params: Dictionary of request parameters
    """
    annotations_json = make_request("/annotations", params=request_params)

    for annotation in annotations_json["results"]:
        print_stats_summary(annotation)

    if args.tsv:
        fetch_and_build_stats_report(args.tsv, request_params, annotations_json)


def fetch_and_build_stats_report(output_file, request_params, annotations_json):
    """
    Fetch statistics data and build stats report.

    Args:
        output_file: Path to output TSV file
        request_params: Dictionary of request parameters
        annotations_json: Already-fetched annotations data
    """
    stats_request_params = request_params.copy()
    stats_request_params.pop("limit", None)

    gene_stats_json = make_request(
        "/annotations/gene-stats", params=stats_request_params
    )
    trans_stats_json = make_request(
        "/annotations/transcript-stats", params=stats_request_params
    )

    build_stats_report(
        output_file,
        annotations_json=annotations_json,
        gene_stats_json=gene_stats_json,
        trans_stats_json=trans_stats_json,
    )


def build_gene_columns(gene_types):
    """
    builder for gene statistics column
    """
    cols = []
    for gene_type in gene_types:
        cols.append(f"{gene_type}.total_count")
        cols.append(f"{gene_type}.length_stats.min")
        cols.append(f"{gene_type}.length_stats.max")
        cols.append(f"{gene_type}.length_stats.mean")

    return cols


def buil_transcript_columns(transcript_types):
    """
    builder for transcript statistics column
    """
    cols = []
    for transcript_type in transcript_types:
        cols.append(f"{transcript_type}.total_count")
        cols.append(f"{transcript_type}.length_stats.min")
        cols.append(f"{transcript_type}.length_stats.max")
        cols.append(f"{transcript_type}.length_stats.mean")
        cols.append(f"{transcript_type}.exons.total_count")
        cols.append(f"{transcript_type}.exon_stats.length.min")
        cols.append(f"{transcript_type}.exon_stats.length.max")
        cols.append(f"{transcript_type}.exon_stats.length.mean")
        cols.append(f"{transcript_type}.exon_stats.concatenated_length.min")
        cols.append(f"{transcript_type}.exon_stats.concatenated_length.max")
        cols.append(f"{transcript_type}.exon_stats.concatenated_length.mean")
        cols.append(f"{transcript_type}.cds_stats.total_count")
        cols.append(f"{transcript_type}.cds_stats.length.min")
        cols.append(f"{transcript_type}.cds_stats.length.max")
        cols.append(f"{transcript_type}.cds_stats.length.mean")
        cols.append(f"{transcript_type}.cds_stats.concatenated_length.min")
        cols.append(f"{transcript_type}.cds_stats.concatenated_length.max")
        cols.append(f"{transcript_type}.cds_stats.concatenated_length.mean")

    return cols


def drop_all_na_columns(header, rows, na="NA", keep_first_n=5):
    """
    Drops columns where every row has NA (or empty) in that column.
    keep_first_n: protect the first N metadata columns from being dropped.
    (This could be optimised)
    """
    if not rows:
        return header, rows

    ncols = len(header)

    # columns to keep (start by keeping metadata columns)
    keep = [True] * ncols
    for j in range(keep_first_n, ncols):
        all_na = True
        for r in rows:
            v = r[j] if j < len(r) else na
            if v not in (na, "", None):
                all_na = False
                break
        keep[j] = not all_na

    new_header = [h for j, h in enumerate(header) if keep[j]]
    new_rows = [[v for j, v in enumerate(r) if keep[j]] for r in rows]
    return new_header, new_rows


def build_stats_report(
    out_file,
    annotations_json={},
    gene_stats_json={},  # gene stats from the endpoint to get set of possible element
    trans_stats_json={},  # same as above but for transcripts
):

    # Prepare header row
    header = [
        "annotation_id",
        "organism_name",
        "taxid",
        "assembly_accession",
        "database",
    ]

    # Get all possible gene and transcript categories
    gene_cols = build_gene_columns([x for x in gene_stats_json["categories"]])
    trans_cols = buil_transcript_columns([x for x in trans_stats_json["types"]])
    header.extend([f"gene.{x}" for x in gene_cols])
    header.extend([f"transcript.{x}" for x in trans_cols])

    rows = []

    for annotation in annotations_json["results"]:
        src = annotation.get("source_file_info", {}) or {}
        features_statistics = annotation.get("features_statistics", {})
        gene_stats = features_statistics.get("gene_category_stats", {})
        trans_stats = features_statistics.get("transcript_type_stats", {})
        # Build basic info row
        row = [
            annotation.get("annotation_id", ""),
            annotation.get("organism_name", ""),
            annotation.get("taxid", ""),
            annotation.get("assembly_accession", ""),
            src.get("database", ""),
        ]

        row.extend(extract_nested_values(gene_stats, gene_cols))
        row.extend(extract_nested_values(trans_stats, trans_cols))

        rows.append(row)

    # Drop cols where all rows are NA
    new_header, new_rows = drop_all_na_columns(header, rows)

    # Write TSV file
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(new_header)
        writer.writerows(new_rows)

    return


def print_stats_summary(d: dict) -> None:
    src = d.get("source_file_info", {}) or {}
    stats = d.get("features_statistics", {}) or {}

    if not stats:
        print("No features_statistics found.")
        return

    def line(k, v):
        return f"{k:<18}: {v}"

    def fmt_int(x):
        return "NA" if x is None else f"{int(x):,}"

    def fmt_float(x, nd=2):
        return "NA" if x is None else f"{float(x):,.{nd}f}"

    def fmt_len_stats(s: Optional[Mapping[str, Any]]) -> str:
        s = dict(s or {})
        return f"min={fmt_int(s.get('min'))}, max={fmt_int(s.get('max'))}, mean={fmt_float(s.get('mean'))}"

    def fmt_counts(dct: dict, sort=True, max_items=None) -> str:
        dct = dct or {}
        items = list(dct.items())
        if sort:
            items.sort(key=lambda kv: (-kv[1], str(kv[0])))
        if max_items is not None and len(items) > max_items:
            shown = items[:max_items]
            rest = len(items) - max_items
            items = shown + [("…", f"(+{rest} more)")]
        return ", ".join(f"{k}={v}" for k, v in items) if items else "—"

    annotation_id = d.get("annotation_id")
    print("-" * 60)
    print(f"Annotation statistics (ID: {annotation_id})")
    print("-" * 60)
    print(line("Organism", d.get("organism_name")))
    print(line("TaxID", d.get("taxid")))
    print(
        line("Assembly", f"{d.get('assembly_accession')}  ({d.get('assembly_name')})")
    )
    print(line("Database", src.get("database")))
    print("-" * 60)

    # --- gene_category_stats ---
    gcs = stats.get("gene_category_stats") or {}
    if gcs:
        print("Gene category stats")
        for cat_name in ("coding", "non_coding"):
            cat = gcs.get(cat_name) or {}
            if not cat:
                continue
            print(indent(f"{cat_name}", "  "))
            print(indent(line("Total genes", fmt_int(cat.get("total_count"))), "    "))

            ls = cat.get("length_stats")
            if ls:
                print(indent(line("Gene length", fmt_len_stats(ls)), "    "))

            bt = cat.get("biotype_counts")
            if bt:
                print(indent("Biotype counts:", "    "))
                print(
                    indent(
                        "\n".join(
                            f"- {k}: {fmt_int(v)}" for k, v in sorted(bt.items())
                        ),
                        "      ",
                    )
                )

            tt = cat.get("transcript_type_counts")
            if tt:
                print(indent("Transcript type counts:", "    "))
                print(
                    indent(
                        "\n".join(
                            f"- {k}: {fmt_int(v)}" for k, v in sorted(tt.items())
                        ),
                        "      ",
                    )
                )

        print("-" * 60)

    # --- transcript_type_stats ---
    tts = stats.get("transcript_type_stats") or {}
    if tts:
        print("Transcript type stats")

        # Sort by total_count desc when present
        def _count_key(k):
            return (-(tts.get(k, {}).get("total_count") or 0), str(k))

        for ttype in sorted(tts.keys(), key=_count_key):
            t = tts.get(ttype) or {}
            print(indent(f"{ttype}", "  "))

            if "total_count" in t:
                print(indent(line("Total", fmt_int(t.get("total_count"))), "    "))

            ls = t.get("length_stats")
            if ls:
                print(indent(line("Length", fmt_len_stats(ls)), "    "))

            bt = t.get("biotype_counts")
            if bt:
                print(indent(line("Biotypes", fmt_counts(bt, sort=True)), "    "))

            ag = t.get("associated_genes") or {}
            if ag:
                print(indent(line("Genes", fmt_int(ag.get("total_count"))), "    "))
                gc = ag.get("gene_categories") or {}
                if gc:
                    print(indent(line("Gene cats", fmt_counts(gc, sort=True)), "    "))

            ex = t.get("exon_stats") or {}
            if ex:
                print(indent("Exons:", "    "))
                if "total_count" in ex:
                    print(
                        indent(
                            line("Total exons", fmt_int(ex.get("total_count"))),
                            "      ",
                        )
                    )
                if ex.get("length"):
                    print(
                        indent(
                            line("Exon length", fmt_len_stats(ex.get("length"))),
                            "      ",
                        )
                    )
                if ex.get("concatenated_length"):
                    print(
                        indent(
                            line(
                                "Concat length",
                                fmt_len_stats(ex.get("concatenated_length")),
                            ),
                            "      ",
                        )
                    )

            cds = t.get("cds_stats") or {}
            if cds:
                print(indent("CDS:", "    "))
                if "total_count" in cds:
                    print(
                        indent(
                            line("Total CDS", fmt_int(cds.get("total_count"))), "      "
                        )
                    )
                if cds.get("length"):
                    print(
                        indent(
                            line("CDS length", fmt_len_stats(cds.get("length"))),
                            "      ",
                        )
                    )
                if cds.get("concatenated_length"):
                    print(
                        indent(
                            line(
                                "Concat length",
                                fmt_len_stats(cds.get("concatenated_length")),
                            ),
                            "      ",
                        )
                    )

            print()  # blank line between transcript types

        print("-" * 60)
