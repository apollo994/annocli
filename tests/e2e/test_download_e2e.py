"""E2E download tests against the live Annotrieve API."""

import pytest

from tests.conftest import ANNOTATION_ID, ANNOTATION_ID2, TAXID, TAXID2
from tests.e2e.helpers import run_annocli

pytestmark = pytest.mark.e2e


def test_download_preview():
    result = run_annocli("download", "--taxids", TAXID, "--mode", "prev")
    assert "Annotations:" in result.stdout


def test_download_links_ref_only():
    result = run_annocli(
        "download", "--taxids", TAXID, "--mode", "links", "--ref-only"
    )
    combined = result.stdout + result.stderr
    assert "wget" in combined or "mkdir" in combined


def test_download_dw_with_assembly(tmp_path):
    out = tmp_path / "downloads"
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
    assert len(gff) > 0
    assert len(fna) > 0


def test_download_preview_annotation_ids():
    result = run_annocli(
        "download",
        "--annotation-ids",
        ANNOTATION_ID,
        ANNOTATION_ID2,
        "--mode",
        "prev",
    )
    assert "Annotations:" in result.stdout


def test_download_preview_taxids_file(tmp_path):
    ids_file = tmp_path / "taxids.txt"
    ids_file.write_text(f"{TAXID}\n{TAXID2}\n")
    result = run_annocli(
        "download", "--taxids-file", str(ids_file), "--mode", "prev"
    )
    assert "Annotations:" in result.stdout


def test_download_preview_annotation_ids_file(tmp_path):
    ids_file = tmp_path / "ann_ids.txt"
    ids_file.write_text(f"{ANNOTATION_ID}\n{ANNOTATION_ID2}\n")
    result = run_annocli(
        "download",
        "--annotation-ids-file",
        str(ids_file),
        "--mode",
        "prev",
    )
    assert "Annotations:" in result.stdout


def test_download_preview_multi_taxids():
    result = run_annocli(
        "download", "--taxids", TAXID, TAXID2, "--mode", "prev"
    )
    assert "Annotations:" in result.stdout


def test_download_mutex_inputs_rejected():
    result = run_annocli(
        "download",
        "--taxids",
        TAXID,
        "--annotation-ids",
        ANNOTATION_ID,
        "--mode",
        "prev",
        check=False,
    )
    assert result.returncode != 0
    assert "[ERROR]" in result.stderr
