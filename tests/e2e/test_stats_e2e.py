"""E2E stats tests against the live Annotrieve API."""

import pytest

from tests.conftest import ANNOTATION_ID, ANNOTATION_ID2, TAXID
from tests.e2e.helpers import run_annocli

pytestmark = pytest.mark.e2e


def test_stats_basic():
    result = run_annocli("stats", "--taxids", TAXID, "--ref-only")
    assert result.stdout.strip() or result.stderr.strip()


def test_stats_tsv(tmp_path):
    tsv = tmp_path / "stats.tsv"
    run_annocli("stats", "--taxids", TAXID, "--ref-only", "--tsv", str(tsv))
    assert tsv.is_file()
    assert tsv.stat().st_size > 0


def test_stats_annotation_ids():
    result = run_annocli(
        "stats", "--annotation-ids", ANNOTATION_ID, ANNOTATION_ID2
    )
    assert result.stdout.strip() or result.stderr.strip()
