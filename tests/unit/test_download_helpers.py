"""Unit tests for download_helpers (TSV-based fetch and processing)."""

from argparse import Namespace
from unittest.mock import MagicMock, patch

from annocli.core.download_helpers import (
    build_annotation_paths,
    fetch_annotation_report,
    handle_download_command,
    process_annotation_result,
)


@patch("annocli.core.download_helpers.fetch_tsv_report")
def test_fetch_annotation_report_without_assemblies(mock_fetch):
    mock_fetch.return_value = [{"annotation_id": "x"}]
    rows = fetch_annotation_report({"taxids": "7460"}, include_assemblies=False)
    mock_fetch.assert_called_once_with({"taxids": "7460"})
    assert rows == [{"annotation_id": "x"}]


@patch("annocli.core.download_helpers.fetch_tsv_report")
def test_fetch_annotation_report_with_assemblies(mock_fetch):
    mock_fetch.return_value = []
    fetch_annotation_report({"taxids": "7460"}, include_assemblies=True)
    mock_fetch.assert_called_once_with(
        {"taxids": "7460", "selected_fields": "assembly_download_url"}
    )


def test_build_annotation_paths_flat_tsv_fields(tmp_path):
    result = {
        "annotation_id": "abc",
        "organism_name": "Apis mellifera",
        "taxid": "7460",
        "database": "RefSeq",
        "assembly_accession": "GCF_1",
    }
    paths = build_annotation_paths(result, str(tmp_path))
    assert paths["annotation_name"] == "Apis_mellifera_7460_RefSeq_GCF_1_abc"
    assert paths["annotation_folder"].endswith("Apis_mellifera_7460/GCF_1")


def test_build_annotation_paths_empty_fields_become_na(tmp_path):
    paths = build_annotation_paths({}, str(tmp_path))
    assert paths["annotation_name"] == "NA_NA_NA_NA_NA"


@patch("annocli.core.download_helpers.download_annotation_file")
@patch("annocli.core.download_helpers.download_assembly_file")
def test_process_annotation_result_dw_with_assembly(
    mock_asm, mock_ann, sample_tsv_row, tmp_path
):
    args = Namespace(
        mode="dw",
        output=str(tmp_path),
        add_asm=True,
        fix_alias=False,
    )
    process_annotation_result(sample_tsv_row, args)
    mock_ann.assert_called_once()
    mock_asm.assert_called_once()
    assert mock_asm.call_args[0][0] == sample_tsv_row["assembly_download_url"]


@patch("annocli.core.download_helpers.download_annotation_file")
@patch("annocli.core.download_helpers.download_assembly_file")
def test_process_annotation_result_skips_empty_assembly_url(
    mock_asm, mock_ann, sample_tsv_row, tmp_path
):
    sample_tsv_row["assembly_download_url"] = ""
    args = Namespace(
        mode="dw",
        output=str(tmp_path),
        add_asm=True,
        fix_alias=False,
    )
    process_annotation_result(sample_tsv_row, args)
    mock_ann.assert_called_once()
    mock_asm.assert_not_called()


@patch("annocli.core.download_helpers.print_download_commands")
def test_process_annotation_result_links_mode(mock_print, sample_tsv_row, tmp_path, capsys):
    args = Namespace(
        mode="links",
        output=str(tmp_path),
        add_asm=True,
        fix_alias=False,
    )
    process_annotation_result(sample_tsv_row, args)
    mock_print.assert_called_once()
    call_kwargs = mock_print.call_args
    assert call_kwargs[0][1] == sample_tsv_row["source_url"]
    assert call_kwargs[0][3] == sample_tsv_row["assembly_download_url"]


def test_handle_download_command_fix_alias_requires_add_asm(capsys):
    args = Namespace(fix_alias=True, add_asm=False, mode="dw", output="out")
    handle_download_command(args, {})
    assert "--fix-alias requires --add-asm" in capsys.readouterr().err


@patch("annocli.core.download_helpers.fetch_annotation_report")
def test_handle_download_command_prev(mock_fetch, capsys):
    mock_fetch.return_value = [{"annotation_id": "a"}, {"annotation_id": "b"}]
    args = Namespace(
        fix_alias=False,
        add_asm=False,
        mode="prev",
        ref_only=True,
        output="out",
    )
    handle_download_command(args, {"taxids": "7460"})
    out = capsys.readouterr().out
    assert "Annotations:" in out
    assert "2" in out
