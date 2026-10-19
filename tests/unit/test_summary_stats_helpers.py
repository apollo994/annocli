"""Unit tests for summary/stats report builders (no network)."""

from annocli.core.stats_helpers import (
    build_gene_columns,
    build_stats_report,
    buil_transcript_columns,
    drop_all_na_columns,
)
from annocli.core.summary_helpers import build_summary_report, make_summary_label


def test_make_summary_label():
    assert make_summary_label("biotypes", ["protein_coding", "lncRNA"]) == [
        "has_biotypes.protein_coding",
        "has_biotypes.lncRNA",
    ]


def test_build_summary_report(tmp_path):
    out = tmp_path / "summary.tsv"
    annotations_json = {
        "results": [
            {
                "annotation_id": "a1",
                "organism_name": "Bee",
                "taxid": "7460",
                "assembly_accession": "GCF_1",
                "assembly_name": "Amel",
                "source_file_info": {
                    "database": "RefSeq",
                    "url_path": "https://example.com/a.gff3.gz",
                    "release_date": "2020-01-01",
                },
                "features_summary": {
                    "has_biotype": True,
                    "has_cds": True,
                    "has_exon": True,
                    "biotypes": ["protein_coding"],
                    "sources": ["RefSeq"],
                    "types": ["gene"],
                },
            }
        ]
    }
    build_summary_report(
        str(out),
        annotations_json=annotations_json,
        biotype_json=["protein_coding", "lncRNA"],
        feature_source_json=["RefSeq"],
        feature_type_json=["gene"],
    )
    text = out.read_text()
    assert "annotation_id" in text
    assert "a1" in text
    assert "has_biotypes.protein_coding" in text.splitlines()[0]


def test_build_gene_and_transcript_columns():
    assert "coding.total_count" in build_gene_columns(["coding"])
    cols = buil_transcript_columns(["mRNA"])
    assert "mRNA.total_count" in cols
    assert "mRNA.exons.total_count" in cols


def test_drop_all_na_columns():
    header = ["a", "b", "c", "d", "e", "f"]
    rows = [
        ["1", "2", "3", "4", "5", "NA"],
        ["1", "2", "3", "4", "5", ""],
    ]
    new_header, new_rows = drop_all_na_columns(header, rows, keep_first_n=5)
    assert "f" not in new_header
    assert all(len(r) == 5 for r in new_rows)


def test_build_stats_report(tmp_path):
    out = tmp_path / "stats.tsv"
    annotations_json = {
        "results": [
            {
                "annotation_id": "a1",
                "organism_name": "Bee",
                "taxid": "7460",
                "assembly_accession": "GCF_1",
                "source_file_info": {"database": "RefSeq"},
                "features_statistics": {
                    "gene_category_stats": {
                        "coding": {
                            "total_count": 10,
                            "length_stats": {"min": 1, "max": 100, "mean": 50},
                        }
                    },
                    "transcript_type_stats": {},
                },
            }
        ]
    }
    build_stats_report(
        str(out),
        annotations_json=annotations_json,
        gene_stats_json={"categories": ["coding"]},
        trans_stats_json={"types": []},
    )
    text = out.read_text()
    assert "annotation_id" in text
    assert "a1" in text
