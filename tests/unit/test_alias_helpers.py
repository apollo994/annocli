"""Unit tests for alias_helpers with tiny GFF/FASTA fixtures."""

import gzip

from annocli.core.alias_helpers import (
    read_assembly_names,
    rewrite_gff_seqids_from_assembly,
)


def _write_gz(path, text):
    with gzip.open(path, "wt") as f:
        f.write(text)


def test_read_assembly_names(tmp_path):
    fasta = tmp_path / "asm.fna.gz"
    _write_gz(fasta, ">CM113805.1 desc\nATGC\n>chr2\nGGCC\n")
    names = read_assembly_names(str(fasta))
    assert "CM113805.1" in names
    assert "chr2" in names


def test_rewrite_gff_seqids_via_region_alias(tmp_path):
    """Tier 1: region Alias attribute maps seqid to assembly name."""
    asm = tmp_path / "asm.fna.gz"
    gff = tmp_path / "ann.gff3.gz"
    out = tmp_path / "out.gff3.gz"

    _write_gz(asm, ">CM113805.1\nATGCATGC\n")
    _write_gz(
        gff,
        "##gff-version 3\n"
        "##sequence-region scaffold_1 1 8\n"
        "scaffold_1\t.\tregion\t1\t8\t.\t+\t.\tID=region1;Alias=CM113805.1\n"
        "scaffold_1\t.\tgene\t1\t4\t.\t+\t.\tID=g1\n",
    )

    mapping = rewrite_gff_seqids_from_assembly(str(gff), str(asm), str(out))
    assert mapping.get("scaffold_1") == "CM113805.1"

    with gzip.open(out, "rt") as f:
        content = f.read()
    assert "CM113805.1\t.\tgene\t1\t4" in content
