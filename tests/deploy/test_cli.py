import re

import pytest

from constrained_albc.deploy.__main__ import build_parser, list_specs_text, resolve_out_dir


def test_parser_has_core_args():
    p = build_parser()
    ns = p.parse_args(["--spec", "student_tcn", "--ckpt", "/a.pt", "--out", "/o"])
    assert ns.spec == "student_tcn"
    assert ns.ckpt == "/a.pt"
    assert ns.out == "/o"


def test_list_specs_mentions_both():
    txt = list_specs_text()
    assert "student_tcn" in txt
    assert "teacher_actor" in txt


def test_batch_arg_parses():
    p = build_parser()
    ns = p.parse_args([
        "--batch", "attitude_only_5000",
        "--student-ckpt", "/s.pt", "--teacher-ckpt", "/t.pt", "--out", "/o",
    ])
    assert ns.batch == "attitude_only_5000"
    assert ns.student_ckpt == "/s.pt"
    assert ns.teacher_ckpt == "/t.pt"


def test_golden_flag_parses():
    ns = build_parser().parse_args([
        "--batch", "attitude_only_5000",
        "--student-ckpt", "/s.pt", "--teacher-ckpt", "/t.pt", "--out", "/o", "--golden",
    ])
    assert ns.golden is True


def test_default_out_derives_group_tag_ts():
    """--out omitted -> deploy/<run_group>/<tag>_<ts> (label-before-date, RUN_TS_FORMAT)."""
    ns = build_parser().parse_args([
        "--batch", "attitude_only_5000",
        "--student-ckpt", "/s.pt", "--teacher-ckpt", "/t.pt",
        "--run-group", "attitude_only_campaign", "--tag", "pack_5000iter",
    ])
    out = resolve_out_dir(ns)
    assert re.fullmatch(r"deploy/attitude_only_campaign/pack_5000iter_\d{6}_\d{6}", out)


def test_explicit_out_wins_over_derivation():
    ns = build_parser().parse_args(["--spec", "student_tcn", "--ckpt", "/a.pt", "--out", "/o"])
    assert resolve_out_dir(ns) == "/o"


def test_no_out_and_no_group_tag_exits():
    ns = build_parser().parse_args(["--spec", "student_tcn", "--ckpt", "/a.pt"])
    with pytest.raises(SystemExit):
        resolve_out_dir(ns)
