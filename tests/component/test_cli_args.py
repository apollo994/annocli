"""Component tests: every CLI argument and error path (no live network)."""

from argparse import Namespace
from unittest.mock import patch

import pytest

from annocli.cli import build_parser, build_request_params
from annocli.core.general_helpers import resolve_input_ids


@pytest.fixture
def parser():
    return build_parser()


# --- Global ---


def test_help_exits_zero(parser):
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])
    assert exc.value.code == 0


def test_version_exits_zero(parser):
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0


def test_no_command_prints_help_path(parser):
    args = parser.parse_args([])
    assert args.command is None


# --- download flags ---


def test_download_taxids(parser):
    args = parser.parse_args(["download", "--taxids", "7460", "30192"])
    assert args.command == "download"
    assert args.taxids == ["7460", "30192"]
    assert args.mode == "dw"
    assert args.output == "annotation_downloads"
    assert args.ref_only is False
    assert args.add_asm is False
    assert args.fix_alias is False


def test_download_taxids_file(parser):
    args = parser.parse_args(["download", "--taxids-file", "/tmp/ids.txt"])
    assert args.taxids_file == "/tmp/ids.txt"


def test_download_annotation_ids(parser):
    args = parser.parse_args(
        ["download", "--annotation-ids", "abc", "def", "--mode", "prev"]
    )
    assert args.annotation_ids == ["abc", "def"]
    assert args.mode == "prev"


def test_download_annotation_ids_file(parser):
    args = parser.parse_args(
        ["download", "--annotation-ids-file", "/tmp/ann.txt"]
    )
    assert args.annotation_ids_file == "/tmp/ann.txt"


@pytest.mark.parametrize("mode", ["dw", "prev", "links"])
def test_download_mode_choices(parser, mode):
    args = parser.parse_args(["download", "--taxids", "7460", "--mode", mode])
    assert args.mode == mode


def test_download_invalid_mode(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["download", "--taxids", "7460", "--mode", "nope"])


def test_download_ref_only(parser):
    args = parser.parse_args(["download", "--taxids", "7460", "--ref-only"])
    assert args.ref_only is True
    params = build_request_params(args)
    assert params["refseq_categories"] == "reference genome"
    assert params["limit"] == 1000


def test_download_add_asm_and_fix_alias(parser):
    args = parser.parse_args(
        ["download", "--taxids", "7460", "--add-asm", "--fix-alias"]
    )
    assert args.add_asm is True
    assert args.fix_alias is True


def test_download_output_short_and_long(parser):
    args = parser.parse_args(["download", "--taxids", "7460", "-o", "out_dir"])
    assert args.output == "out_dir"
    args2 = parser.parse_args(
        ["download", "--taxids", "7460", "--output", "other"]
    )
    assert args2.output == "other"


def test_download_ref_only_absent_no_refseq_param(parser):
    args = parser.parse_args(["download", "--taxids", "7460"])
    params = build_request_params(args)
    assert "refseq_categories" not in params


# --- summary flags ---


def test_summary_taxids_and_tsv(parser):
    args = parser.parse_args(
        ["summary", "--taxids", "7460", "--ref-only", "--tsv", "s.tsv"]
    )
    assert args.command == "summary"
    assert args.taxids == ["7460"]
    assert args.ref_only is True
    assert args.tsv == "s.tsv"
    assert build_request_params(args)["refseq_categories"] == "reference genome"


def test_summary_taxids_file(parser):
    args = parser.parse_args(["summary", "--taxids-file", "t.txt"])
    assert args.taxids_file == "t.txt"


def test_summary_annotation_ids(parser):
    args = parser.parse_args(["summary", "--annotation-ids", "abc"])
    assert args.annotation_ids == ["abc"]


def test_summary_annotation_ids_file(parser):
    args = parser.parse_args(["summary", "--annotation-ids-file", "a.txt"])
    assert args.annotation_ids_file == "a.txt"


# --- stats flags ---


def test_stats_taxids_and_tsv(parser):
    args = parser.parse_args(
        ["stats", "--taxids", "7460", "--ref-only", "--tsv", "st.tsv"]
    )
    assert args.command == "stats"
    assert args.tsv == "st.tsv"
    assert args.ref_only is True


def test_stats_taxids_file(parser):
    args = parser.parse_args(["stats", "--taxids-file", "t.txt"])
    assert args.taxids_file == "t.txt"


def test_stats_annotation_ids(parser):
    args = parser.parse_args(["stats", "--annotation-ids", "abc", "def"])
    assert args.annotation_ids == ["abc", "def"]


def test_stats_annotation_ids_file(parser):
    args = parser.parse_args(["stats", "--annotation-ids-file", "a.txt"])
    assert args.annotation_ids_file == "a.txt"


# --- alias flags ---


def test_alias_positionals_and_output(parser):
    args = parser.parse_args(
        ["alias", "ann.gff3.gz", "asm.fna.gz", "--output", "out.gff3.gz"]
    )
    assert args.command == "alias"
    assert args.annotation == "ann.gff3.gz"
    assert args.assembly == "asm.fna.gz"
    assert args.output == "out.gff3.gz"


def test_alias_output_default_none(parser):
    args = parser.parse_args(["alias", "ann.gff3.gz", "asm.fna.gz"])
    assert args.output is None


# --- input wiring / errors ---


def test_request_params_taxids_wiring(parser):
    """Simulate main() input wiring with mocked validators."""
    args = parser.parse_args(["download", "--taxids", "7460", "30192", "--ref-only"])
    params = build_request_params(args)
    with patch(
        "annocli.core.general_helpers.core_request",
        return_value={"total": 1, "results": [{}]},
    ):
        mode, ids = resolve_input_ids(args)
        assert mode == "taxids"
        from annocli.core.general_helpers import validate_taxids

        valid = validate_taxids(ids)
        params["taxids"] = ",".join(valid)
    assert params["taxids"] == "7460,30192"
    assert params["refseq_categories"] == "reference genome"


def test_request_params_md5_wiring(parser):
    args = parser.parse_args(["summary", "--annotation-ids", "abc123"])
    params = build_request_params(args)
    with patch(
        "annocli.core.general_helpers.core_request",
        return_value={"total": 1, "results": [{}]},
    ):
        mode, ids = resolve_input_ids(args)
        assert mode == "annotation_ids"
        from annocli.core.general_helpers import validate_annotation_ids

        valid = validate_annotation_ids(ids)
        params["md5_checksums"] = ",".join(valid)
    assert params["md5_checksums"] == "abc123"
    assert "refseq_categories" not in params


def test_mutex_taxids_and_annotation_ids(parser, capsys):
    args = parser.parse_args(
        ["download", "--taxids", "7460", "--annotation-ids", "abc", "--mode", "prev"]
    )
    with pytest.raises(SystemExit):
        resolve_input_ids(args)
    assert "mutually exclusive" in capsys.readouterr().err


def test_no_input_error(parser, capsys):
    args = parser.parse_args(["download", "--mode", "prev"])
    with pytest.raises(SystemExit):
        resolve_input_ids(args)
    assert "No input provided" in capsys.readouterr().err


def test_fix_alias_without_add_asm_handler_error(capsys):
    from annocli.core.download_helpers import handle_download_command

    args = Namespace(fix_alias=True, add_asm=False, mode="dw", output="out")
    handle_download_command(args, {})
    assert "--fix-alias requires --add-asm" in capsys.readouterr().err
