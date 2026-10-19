"""Shared fixtures and constants for annocli tests."""

import pytest

# Live-API fixtures (same organisms/ids used by test.sh)
TAXID = "7460"
TAXID2 = "30192"
ANNOTATION_ID = "1d7a323a9ccc520dc1dba53fd58466fd"
ANNOTATION_ID2 = "0cfb74797a4da143b604e03e1139f98d"


@pytest.fixture
def sample_tsv_row():
    return {
        "annotation_id": "abc123",
        "organism_name": "Apis mellifera",
        "taxid": "7460",
        "database": "RefSeq",
        "assembly_accession": "GCF_000002195.4",
        "source_url": "https://example.com/ann.gff3.gz",
        "assembly_download_url": "https://example.com/asm.fna.gz",
    }
