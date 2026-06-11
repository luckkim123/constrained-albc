from constrained_albc.deploy.__main__ import build_parser, list_specs_text


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
