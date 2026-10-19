"""E2E alias tests against files downloaded from the live API."""

from pathlib import Path

import pytest

from tests.conftest import TAXID
from tests.e2e.helpers import run_annocli

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def downloaded_pair(tmp_path_factory):
    out = tmp_path_factory.mktemp("alias_download")
    run_annocli(
        "download",
        "--taxids",
        TAXID,
        "--ref-only",
        "--add-asm",
        "-o",
        str(out),
    )
    gff = list(out.rglob("*.gff.gz")) + list(out.rglob("*.gff3.gz"))
    fna = list(out.rglob("*.fna.gz"))
    if not gff or not fna:
        pytest.skip("Download did not produce GFF and FNA for alias test")
    return gff[0], fna[0]


def test_alias_creates_output_and_mapping(downloaded_pair, tmp_path):
    gff, fna = downloaded_pair
    out_gff = tmp_path / "test_alias.gff3.gz"
    run_annocli("alias", str(gff), str(fna), "--output", str(out_gff))
    assert out_gff.is_file() and out_gff.stat().st_size > 0
    mapping = Path(f"{out_gff}.aliasMappings.tsv")
    assert mapping.is_file()
