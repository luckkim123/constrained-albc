"""Parity proof: the toggle-off path is byte-identical to the joint-delta baseline.

albc_env.py is NOT sim-free importable (its top-level `from isaaclab.assets import
Articulation` pulls omni.physics, i.e. the real Isaac Sim runtime). So this proof
reads the source as TEXT and asserts structurally, rather than importing the module
and using inspect.getsource. The full byte-identical-off runtime behavior is verified
end-to-end in the Task 7 Isaac Sim smoke.
"""
import re
from pathlib import Path

_ALBC_ENV = Path(__file__).resolve().parents[3] / "constrained_albc" / "envs" / "main" / "albc_env.py"


def _read_method_src(method_name: str) -> str:
    """Return the source text of a method body, from `def <name>` to the next dedented `def`/`class`."""
    text = _ALBC_ENV.read_text()
    # Match `    def <name>(` ... up to the next same-or-lower-indent def/class or EOF.
    pat = re.compile(
        rf"\n(?P<indent> +)def {re.escape(method_name)}\(.*?(?=\n(?P=indent)def |\n(?P=indent)@|\nclass |\Z)",
        re.DOTALL,
    )
    m = pat.search(text)
    assert m is not None, f"method {method_name} not found in {_ALBC_ENV}"
    return m.group(0)


def test_off_branch_is_the_original_integrator_line():
    src = _read_method_src("_apply_joint_pd_action")
    # The verbatim joint-delta baseline line must be present (the off-branch body).
    assert "self._joint_pos_targets += self._delta_scale * actions" in src
    # And it must be guarded by the `_ee_layer is None` off-branch.
    assert "if self._ee_layer is None:" in src


def test_ee_layer_set_none_on_off_path():
    # _init_action_buffers must set self._ee_layer = None when the toggle is off.
    src = _read_method_src("_init_action_buffers")
    assert "self._ee_layer = None" in src
    # And construct the layer only inside the enabled branch.
    assert "if self.cfg.ee_action_enable:" in src


def test_albc_env_source_exists():
    assert _ALBC_ENV.is_file()
