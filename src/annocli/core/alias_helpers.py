import gzip
import subprocess


def rewrite_gff_seqids_from_assembly(
    ann_gff_gz: str,
    asm_fna_gz: str,
    out_gff_gz: str,
) -> dict:
    """
    Rewrite the 1st column (seqid) of a .gff3.gz using region Alias values, so that seqids
    match the sequence names present in the assembly FASTA (.fna.gz).
    
    Returns:
      names_mapping (dict): mapping from original seqid -> alias (may be None if missing)
    """

    def _run_bash(cmd: str) -> str:
        return subprocess.run(
            ["bash", "-lc", cmd],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout

    def _sh_quote(s: str) -> str:
        return "'" + s.replace("'", "'\"'\"'") + "'"
    
    ann_zip = ann_gff_gz.endswith(".gz")
    asm_zip = asm_fna_gz.endswith(".gz")
    out_zip = out_gff_gz.endswith(".gz")

    ann_cat = "gzip -cd" if ann_zip else "cat"
    asm_cat = "gzip -cd" if asm_zip else "cat"

    # 1) Assembly names via grep/sed/awk
    asm_cmd = (
        f"{asm_cat} {_sh_quote(asm_fna_gz)} | "
        "grep '^>' | sed 's/^>//' | awk '{print $1}'"
    )
    asm_names = {x.strip() for x in _run_bash(asm_cmd).splitlines() if x.strip()}

    # 2) Region lines via awk
    region_cmd = (
        f"{ann_cat} {_sh_quote(ann_gff_gz)} | "
        "awk -F'\t' '$3==\"region\" {print}'"
    )
    region_lines = [x for x in _run_bash(region_cmd).splitlines() if x and not x.startswith("#")]

    names_mapping = {}
    for region in region_lines:
        parts = region.split("\t")
        if len(parts) < 9:
            continue
        current_name = parts[0]
        attr_field = parts[8]
        attrs = dict(kv.split("=", 1) for kv in attr_field.split(";") if "=" in kv)
        alias = attrs.get("Alias",'NA')
        if len(alias.split(',')) == 1: 
            names_mapping[current_name] = alias
        else:
            aliases = alias.split(',')
            for a in aliases:
                if a in asm_names:
                    names_mapping[current_name] = a


    # 3) Rewrite GFF

    ann_open = gzip.open if ann_zip else open
    out_open = gzip.open if out_zip else open

    with ann_open(ann_gff_gz, "rt", encoding="utf-8", errors="replace") as ann_in, \
         out_open(out_gff_gz, "wt", encoding="utf-8", errors="replace") as ann_out:

        for line in ann_in:
            if line.startswith("#") or not line.strip():
                continue

            cols = line.rstrip("\n").split("\t")
            if len(cols) < 9:
                ann_out.write(line)
                continue

            seq_name = cols[0]
            if seq_name in asm_names:
                ann_out.write(line)
            else:
                new_name = names_mapping.get(seq_name)
                if not new_name:
                    # If no alias mapping exists, keep original (safer than crashing)
                    ann_out.write(line)
                    continue
                cols[0] = new_name
                ann_out.write("\t".join(cols) + "\n")

    return names_mapping

