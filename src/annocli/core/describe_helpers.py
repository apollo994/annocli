from textwrap import indent


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
