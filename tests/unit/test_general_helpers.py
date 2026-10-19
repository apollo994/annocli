"""Unit tests for general_helpers."""

from argparse import Namespace
from unittest.mock import patch

import pytest

from annocli.core.general_helpers import (
    get_file_extension_parts,
    get_nested_dict_value,
    extract_nested_values,
    insert_suffix_before_extension,
    read_ids_from_file,
    resolve_input_ids,
    validate_annotation_ids,
    validate_taxids,
    write_tsv_mapping,
)


def test_get_file_extension_parts_gz():
    assert get_file_extension_parts("file.gff3.gz") == ["gff3", "gz"]


def test_get_file_extension_parts_plain():
    assert get_file_extension_parts("file.gff3") == ["gff3"]


def test_insert_suffix_before_extension_gz():
    assert (
        insert_suffix_before_extension("file.gff3.gz", "aliasMatch")
        == "file.aliasMatch.gff3.gz"
    )


def test_insert_suffix_before_extension_plain():
    assert insert_suffix_before_extension("file.gff3", "filtered") == "file.filtered.gff3"


def test_write_tsv_mapping(tmp_path):
    out = tmp_path / "map.tsv"
    write_tsv_mapping({"chr1": "NC_1", "chr2": "NC_2"}, str(out))
    assert out.read_text() == "chr1\tNC_1\nchr2\tNC_2\n"


def test_get_nested_dict_value():
    d = {"a": {"b": {"c": 1}}}
    assert get_nested_dict_value(d, "a.b.c") == 1
    assert get_nested_dict_value(d, "a.b.x", default="N/A") == "N/A"


def test_extract_nested_values():
    d = {"stats": {"min": 1, "max": 9}}
    assert extract_nested_values(d, ["stats.min", "stats.max"]) == [1, 9]


def test_read_ids_from_file(tmp_path):
    f = tmp_path / "ids.txt"
    f.write_text("7460\n\n30192\n")
    assert read_ids_from_file(str(f)) == ["7460", "30192"]


def test_resolve_input_ids_taxids():
    args = Namespace(
        taxids=["7460", "30192"],
        taxids_file=None,
        annotation_ids=None,
        annotation_ids_file=None,
    )
    mode, ids = resolve_input_ids(args)
    assert mode == "taxids"
    assert ids == ["7460", "30192"]


def test_resolve_input_ids_from_file(tmp_path):
    f = tmp_path / "taxids.txt"
    f.write_text("7460\n")
    args = Namespace(
        taxids=None,
        taxids_file=str(f),
        annotation_ids=None,
        annotation_ids_file=None,
    )
    mode, ids = resolve_input_ids(args)
    assert mode == "taxids"
    assert ids == ["7460"]


def test_resolve_input_ids_annotation_ids():
    args = Namespace(
        taxids=None,
        taxids_file=None,
        annotation_ids=["abc", "def"],
        annotation_ids_file=None,
    )
    mode, ids = resolve_input_ids(args)
    assert mode == "annotation_ids"
    assert ids == ["abc", "def"]


def test_resolve_input_ids_mutex(capsys):
    args = Namespace(
        taxids=["7460"],
        taxids_file=None,
        annotation_ids=["abc"],
        annotation_ids_file=None,
    )
    with pytest.raises(SystemExit) as exc:
        resolve_input_ids(args)
    assert exc.value.code == 1
    assert "mutually exclusive" in capsys.readouterr().err


def test_resolve_input_ids_missing(capsys):
    args = Namespace(
        taxids=None,
        taxids_file=None,
        annotation_ids=None,
        annotation_ids_file=None,
    )
    with pytest.raises(SystemExit) as exc:
        resolve_input_ids(args)
    assert exc.value.code == 1
    assert "No input provided" in capsys.readouterr().err


@patch("annocli.core.general_helpers.core_request")
def test_validate_taxids_filters_empty(mock_core):
    mock_core.side_effect = [
        {"total": 2, "results": [{}]},
        {"total": 0, "results": []},
    ]
    assert validate_taxids(["7460", "99999"]) == ["7460"]


@patch("annocli.core.general_helpers.core_request")
def test_validate_taxids_none_valid(mock_core):
    mock_core.return_value = {"total": 0, "results": []}
    with pytest.raises(SystemExit):
        validate_taxids(["99999"])


@patch("annocli.core.general_helpers.core_request")
def test_validate_annotation_ids(mock_core):
    mock_core.side_effect = [
        {"total": 1, "results": [{}]},
        {"total": 0, "results": []},
    ]
    assert validate_annotation_ids(["good", "bad"]) == ["good"]
