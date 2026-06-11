import numpy as np
import torch
from constrained_albc.deploy.engine import export_from_state_dict
from constrained_albc.deploy.specs.student_tcn import StudentTCNSpec

GT = {
    "channel_transform.0.weight": (32, 69), "channel_transform.0.bias": (32,),
    "conv.0.weight": (64, 32, 3), "conv.0.bias": (64,),
    "conv.2.weight": (128, 64, 3), "conv.2.bias": (128,),
    "conv.4.weight": (128, 128, 3), "conv.4.bias": (128,),
    "head.0.weight": (128, 384), "head.0.bias": (128,),
    "head.2.weight": (128,), "head.2.bias": (128,),
    "head.3.weight": (9, 128), "head.3.bias": (9,),
}


class _FakeStudent(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self._sd = {k: torch.zeros(s, dtype=torch.float32) for k, s in GT.items()}
    def state_dict(self, *a, **k):
        return self._sd


def test_export_from_state_dict_saves_and_verifies(tmp_path):
    spec = StudentTCNSpec()
    report = export_from_state_dict(spec, _FakeStudent(), str(tmp_path))
    out = tmp_path / "weights_tcn.npz"
    assert out.exists()
    assert report.ok
    d = np.load(str(out))
    assert set(d.keys()) == set(GT.keys())
    assert d["channel_transform.0.weight"].dtype == np.float32
