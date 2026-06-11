import numpy as np
import pytest
from constrained_albc.deploy.spec import ShapeSpec, ExportContractError
from constrained_albc.deploy.verify import verify_npz


CONTRACT = {
    "a.weight": ShapeSpec(shape=(2, 3)),
    "a.bias": ShapeSpec(shape=(2,)),
}


def _save(tmp_path, arrays):
    p = tmp_path / "w.npz"
    np.savez(p, **arrays)
    return str(p)


def test_verify_passes_on_exact_contract(tmp_path):
    p = _save(tmp_path, {
        "a.weight": np.zeros((2, 3), np.float32),
        "a.bias": np.zeros((2,), np.float32),
    })
    report = verify_npz(p, CONTRACT)
    assert report.ok
    assert report.errors == []


def test_verify_fails_on_missing_key(tmp_path):
    p = _save(tmp_path, {"a.weight": np.zeros((2, 3), np.float32)})
    with pytest.raises(ExportContractError) as exc:
        verify_npz(p, CONTRACT)
    assert "a.bias" in str(exc.value)


def test_verify_fails_on_extra_key(tmp_path):
    p = _save(tmp_path, {
        "a.weight": np.zeros((2, 3), np.float32),
        "a.bias": np.zeros((2,), np.float32),
        "junk": np.zeros((1,), np.float32),
    })
    with pytest.raises(ExportContractError) as exc:
        verify_npz(p, CONTRACT)
    assert "junk" in str(exc.value)


def test_verify_fails_on_wrong_shape(tmp_path):
    p = _save(tmp_path, {
        "a.weight": np.zeros((2, 99), np.float32),  # wrong
        "a.bias": np.zeros((2,), np.float32),
    })
    with pytest.raises(ExportContractError) as exc:
        verify_npz(p, CONTRACT)
    assert "shape" in str(exc.value).lower()


def test_verify_fails_on_wrong_dtype(tmp_path):
    p = _save(tmp_path, {
        "a.weight": np.zeros((2, 3), np.float64),  # wrong
        "a.bias": np.zeros((2,), np.float32),
    })
    with pytest.raises(ExportContractError) as exc:
        verify_npz(p, CONTRACT)
    assert "dtype" in str(exc.value).lower()
