"""Unit tests for requests helpers."""

from unittest.mock import MagicMock, patch

import pytest

from annocli.core.requests import API_BASE_URL, fetch_tsv_report, make_request


@patch("annocli.core.requests.core_request")
def test_make_request_no_pagination(mock_core):
    mock_core.return_value = {"results": [{"a": 1}], "total": 1}
    out = make_request("/annotations", params={"limit": 10})
    assert out["results"] == [{"a": 1}]
    assert mock_core.call_count == 1


@patch("annocli.core.requests.core_request")
def test_make_request_paginates(mock_core):
    mock_core.side_effect = [
        {"results": [{"id": 1}], "total": 2},
        {"results": [{"id": 2}], "total": 2},
    ]
    out = make_request("/annotations", params={"limit": 1})
    assert [r["id"] for r in out["results"]] == [1, 2]
    assert mock_core.call_count == 2


@patch("annocli.core.requests.requests.post")
def test_fetch_tsv_report_parses_rows(mock_post):
    tsv = (
        "annotation_id\tassembly_accession\tsource_url\n"
        "abc\tGCF_1\thttps://example.com/a.gff3.gz\n"
        "def\tGCF_2\thttps://example.com/b.gff3.gz\n"
    )
    response = MagicMock()
    response.encoding = "utf-8"
    response.iter_lines.return_value = tsv.splitlines()
    response.raise_for_status = MagicMock()
    mock_post.return_value = response

    rows = fetch_tsv_report({"taxids": "7460"})

    mock_post.assert_called_once()
    assert mock_post.call_args[0][0] == f"{API_BASE_URL}/annotations/report"
    assert mock_post.call_args[1]["json"] == {"taxids": "7460"}
    assert mock_post.call_args[1]["stream"] is True
    assert len(rows) == 2
    assert rows[0]["annotation_id"] == "abc"
    assert rows[1]["source_url"] == "https://example.com/b.gff3.gz"


@patch("annocli.core.requests.requests.post")
def test_fetch_tsv_report_raises_on_http_error(mock_post):
    import requests as req

    mock_post.side_effect = req.exceptions.RequestException("boom")
    with pytest.raises(ValueError, match="Request failed"):
        fetch_tsv_report({})
