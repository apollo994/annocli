"""E2E summary tests against the live Annotrieve API."""

import pytest

from tests.conftest import ANNOTATION_ID, ANNOTATION_ID2, TAXID
from tests.e2e.helpers import run_annocli

pytestmark = pytest.mark.e2e


def test_summary_basic():
    result = run_annocli("summary", "--taxids", TAXID, "--ref-only")
    combined = (result.stdout + result.stderr).lower()
    assert any(
        token in combined for token in ("organism", "assembly", "taxid", "feature")
    )


def test_summary_tsv(tmp_path):
    tsv = tmp_path / "summary.tsv"
    run_annocli(
        "summary", "--taxids", TAXID, "--ref-only", "--tsv", str(tsv)
    )
    assert tsv.is_file()
    assert tsv.stat().st_size > 0


def test_summary_annotation_ids():
    result = run_annocli(
        "summary", "--annotation-ids", ANNOTATION_ID, ANNOTATION_ID2
    )
    combined = (result.stdout + result.stderr).lower()
    assert any(
        token in combined for token in ("organism", "assembly", "taxid", "feature")
    )
