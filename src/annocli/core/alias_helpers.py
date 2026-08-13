"""
Match annotation sequence IDs (GFF column 1) to the sequence names used in an
assembly FASTA.

Resolution is a ladder. Each tier only looks at the seqids earlier tiers could
not resolve, and no tier is allowed to rename on an ambiguous guess:

    tier 0  the seqid is already an assembly name  -> nothing to do
    tier 1  Alias attribute of a GFF ``region`` feature
    tier 2  local name normalisation (INSDC version suffix, ``chr`` prefix,
            mitochondrion spellings, case)

Tier 1 is what Ensembl and NCBI annotations provide. Tier 2 exists because some
producers (TOGA, lifted-over or bespoke GFFs) ship no ``region`` features at
all, leaving tier 1 with nothing to work with.
"""

import gzip
import re
import sys

from .general_helpers import insert_suffix_before_extension, write_tsv_mapping

# INSDC accessions carry a version suffix in the FASTA (CM113805.1) that
# annotation producers often drop (CM113805).
_VERSION_SUFFIX = re.compile(r"\.\d+$")

_MITOCHONDRION = {"m", "mt", "mito", "mitochondrion"}


def handle_alias_command(args):
    """
    Handle the alias command logic.

    Args:
        args: Parsed command-line arguments with annotation, assembly, and output
    """
    output_path = args.output

    if output_path is None:
        output_path = insert_suffix_before_extension(args.annotation, "aliasMatch")

    alias_mapping = rewrite_gff_seqids_from_assembly(
        args.annotation,
        args.assembly,
        output_path,
    )

    alias_report = f"{output_path}.aliasMappings.tsv"
    write_tsv_mapping(alias_mapping, alias_report)


def _open_text(path, mode):
    """Open a plain or gzipped file in text mode, based on the .gz extension."""
    opener = gzip.open if path.endswith(".gz") else open
    return opener(path, mode, encoding="utf-8", errors="replace")


def _parse_attributes(attr_field):
    """
    Parse a GFF3 column 9 attribute string into a dict.

    Malformed entries (no '=') are skipped rather than raising.
    """
    attrs = {}
    for entry in attr_field.strip().rstrip(";").split(";"):
        entry = entry.strip()
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        attrs[key.strip()] = value.strip()
    return attrs


def _normalise_name(name):
    """
    Reduce a sequence name to a comparison key (tier 2).

    Applied identically to both annotation and assembly names, so it only has to
    be consistent, not canonical:

        CM113805.1 -> cm113805      (INSDC version suffix dropped)
        chr1       -> 1            (UCSC-style prefix dropped)
        chrM, MT   -> mt           (mitochondrion spellings unified)
    """
    key = _VERSION_SUFFIX.sub("", name.strip().lower())
    if key.startswith("chr"):
        key = key[3:]
    if key in _MITOCHONDRION:
        key = "mt"
    return key


def read_assembly_names(asm_path):
    """
    Collect sequence names from an assembly FASTA.

    Only the first whitespace-separated token of each header is kept, which is
    the name the GFF is expected to use.
    """
    names = set()
    with _open_text(asm_path, "rt") as fasta:
        for line in fasta:
            if not line.startswith(">"):
                continue
            header = line[1:].split()
            if header:
                names.add(header[0])
    return names


def scan_annotation(ann_path, asm_names):
    """
    Single pass over the GFF collecting what resolution needs.

    Returns:
        seqids (list): distinct column 1 values, in order of first appearance
        region_aliases (dict): seqid -> alias, for tier 1

    An Alias is only accepted from a ``region`` feature, and only if it names a
    sequence that is actually present in the assembly.
    """
    seqids = []
    seen = set()
    region_aliases = {}

    with _open_text(ann_path, "rt") as annotation:
        for line in annotation:
            if line.startswith("#") or not line.strip():
                continue

            cols = line.rstrip("\n").split("\t")
            if len(cols) < 9:
                continue

            seqid = cols[0]
            if seqid not in seen:
                seen.add(seqid)
                seqids.append(seqid)

            if cols[2] != "region":
                continue

            alias = _parse_attributes(cols[8]).get("Alias")
            if not alias:
                continue

            for candidate in alias.split(","):
                candidate = candidate.strip()
                if candidate in asm_names:
                    region_aliases[seqid] = candidate
                    break

    return seqids, region_aliases


def _build_normalised_index(asm_names):
    """
    Index assembly names by their normalised key, dropping collisions.

    If two assembly sequences share a key (an assembly holding both 'chr1' and
    '1', say) that key cannot identify either of them, so it is removed
    entirely instead of resolving to an arbitrary one.

    Returns:
        index (dict): key -> unambiguous assembly name
        ambiguous (set): keys claimed by more than one assembly name
    """
    index = {}
    ambiguous = set()

    for name in asm_names:
        key = _normalise_name(name)
        if key in index and index[key] != name:
            ambiguous.add(key)
        else:
            index[key] = name

    for key in ambiguous:
        index.pop(key, None)

    return index, ambiguous


def _resolve_by_normalisation(unresolved, asm_names, claimed):
    """
    Tier 2: match leftover seqids to assembly names through _normalise_name.

    A rename is only proposed when the key is unambiguous on both sides: one
    assembly name claims it, and one annotation seqid asks for it. Anything else
    is reported and left alone, because a wrong seqid silently invalidates every
    coordinate on it.

    Args:
        unresolved: seqids tiers 0 and 1 could not place
        asm_names: every sequence name in the assembly
        claimed: assembly names an earlier tier already assigned to some seqid;
            reusing one would merge two distinct sequences into a single name
    """
    index, ambiguous_targets = _build_normalised_index(asm_names)

    by_key = {}
    for seqid in unresolved:
        by_key.setdefault(_normalise_name(seqid), []).append(seqid)

    mapping = {}
    for key, seqids in by_key.items():
        names = ", ".join(sorted(seqids))

        if key in ambiguous_targets:
            print(
                f"[WARNING] not renaming {names}: several assembly sequences "
                f"share the normalised name '{key}'",
                file=sys.stderr,
            )
            continue

        if len(seqids) > 1:
            print(
                f"[WARNING] not renaming {names}: they share the normalised "
                f"name '{key}'",
                file=sys.stderr,
            )
            continue

        target = index.get(key)
        if target is None:
            continue

        if target in claimed:
            print(
                f"[WARNING] not renaming {names}: '{target}' is already used by "
                "another sequence in the annotation",
                file=sys.stderr,
            )
            continue

        mapping[seqids[0]] = target

    return mapping


def resolve_seqids(seqids, asm_names, region_aliases):
    """
    Walk the resolution ladder and return the renames to apply.

    Returns:
        mapping (dict): seqid -> assembly name, only for seqids that need one
        unresolved (list): seqids no tier could match
    """
    mapping = {}
    unresolved = []

    for seqid in seqids:
        if seqid in asm_names:
            continue  # tier 0: already correct

        alias = region_aliases.get(seqid)  # tier 1
        if alias:
            mapping[seqid] = alias
        else:
            unresolved.append(seqid)

    if unresolved:
        # Names an earlier tier already spoke for, either because the seqid was
        # correct to begin with or because tier 1 mapped something onto it.
        claimed = {s for s in seqids if s in asm_names} | set(mapping.values())
        normalised = _resolve_by_normalisation(unresolved, asm_names, claimed)  # tier 2
        mapping.update(normalised)
        unresolved = [s for s in unresolved if s not in normalised]

    return mapping, unresolved


def rewrite_gff(ann_path, out_path, mapping):
    """
    Copy the GFF through, substituting seqids found in mapping.

    Comments, pragmas and blank lines are preserved so the output stays a valid
    GFF3; ``##sequence-region`` carries a seqid of its own and is rewritten too.
    """
    with _open_text(ann_path, "rt") as annotation, _open_text(out_path, "wt") as out:
        for line in annotation:
            if line.startswith("##sequence-region"):
                out.write(_rewrite_sequence_region(line, mapping))
                continue

            if line.startswith("#") or not line.strip():
                out.write(line)
                continue

            cols = line.rstrip("\n").split("\t")
            if len(cols) < 9:
                out.write(line)
                continue

            new_name = mapping.get(cols[0])
            if new_name is None:
                out.write(line)
                continue

            cols[0] = new_name
            out.write("\t".join(cols) + "\n")


def _rewrite_sequence_region(line, mapping):
    """Rewrite the seqid of a '##sequence-region seqid start end' pragma."""
    parts = line.split()
    if len(parts) < 2:
        return line

    new_name = mapping.get(parts[1])
    if new_name is None:
        return line

    parts[1] = new_name
    return " ".join(parts) + "\n"


def rewrite_gff_seqids_from_assembly(
    ann_gff_gz: str,
    asm_fna_gz: str,
    out_gff_gz: str,
) -> dict:
    """
    Rewrite the 1st column (seqid) of a GFF so that it matches the sequence
    names present in the assembly FASTA.

    Both inputs and the output may be plain or gzipped, decided per path by the
    .gz extension.

    Returns:
        names_mapping (dict): original seqid -> assembly name, containing only
        the seqids that were actually renamed
    """
    asm_names = read_assembly_names(asm_fna_gz)
    seqids, region_aliases = scan_annotation(ann_gff_gz, asm_names)
    names_mapping, _unresolved = resolve_seqids(seqids, asm_names, region_aliases)
    rewrite_gff(ann_gff_gz, out_gff_gz, names_mapping)

    return names_mapping
