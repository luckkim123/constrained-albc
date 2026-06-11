import pytest
from constrained_albc.deploy.spec import ShapeSpec, ExportSpec, ExportContractError


def test_shapespec_defaults_to_float32():
    s = ShapeSpec(shape=(32, 69))
    assert s.shape == (32, 69)
    assert s.dtype == "float32"


def test_exportspec_is_abstract():
    with pytest.raises(TypeError):
        ExportSpec()  # cannot instantiate ABC with abstract methods


def test_contract_error_is_exception():
    assert issubclass(ExportContractError, Exception)
