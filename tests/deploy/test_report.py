from constrained_albc.deploy.verify import ContractReport
from constrained_albc.deploy.report import build_report


def test_report_contains_guide_fields():
    reports = {
        "student_tcn": ContractReport(
            path="/x/weights_tcn.npz", ok=True, errors=[],
            entries=[("head.3.weight", (9, 128), "float32")],
        ),
        "teacher_actor": ContractReport(
            path="/x/weights_teacher.npz", ok=True, errors=[],
            entries=[("actor.0.weight", (256, 78), "float32")],
        ),
    }
    chosen = {
        "student_tcn": {"file": "student_999.pt", "iter": 999,
                        "rationale": "last of 1000 (0-indexed)"},
        "teacher_actor": {"file": "model_4999.pt", "iter": 4999,
                          "rationale": "max iter; 5000 absent"},
    }
    md = build_report(reports, chosen, out_dir="/x", mount_status="overlay (docker cp)",
                      golden_status="skipped: obs-assembly lives in env")
    assert "student_999.pt" in md
    assert "model_4999.pt" in md
    assert "4999" in md
    assert "78" in md
    assert "docker cp" in md
    assert "skipped" in md.lower()
