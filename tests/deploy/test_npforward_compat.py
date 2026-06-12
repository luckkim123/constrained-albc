"""npforward.py must stay Python 2.7-loadable.

The board's ROS (lunar rospy) pins the RL inference node to py2.7, so any
py3-only syntax in npforward.py is a deploy-time SyntaxError at `import`.
Found 2026-06-12 on agent-jetson: `@` matmul (PEP 465, py3.5+) killed the
node; every parity check until then had run under python3 (test_npforward.py),
which can never catch a py2-syntax break. This AST gate makes the constraint
permanent: np.dot only, no f-strings, no annotations, no keyword-only args.
"""
import ast
import os

_SRC = os.path.join(os.path.dirname(__file__), "..", "..",
                    "constrained_albc", "deploy", "npforward.py")


def _tree():
    with open(_SRC) as f:
        return ast.parse(f.read())


def test_no_matmul_operator():
    hits = [n for n in ast.walk(_tree()) if isinstance(n, ast.MatMult)]
    assert hits == [], "@ matmul is py3.5+ only; board rospy is py2.7 -- use np.dot"


def test_no_fstrings():
    hits = [n for n in ast.walk(_tree()) if isinstance(n, ast.JoinedStr)]
    assert hits == [], "f-strings are py3.6+ only; board rospy is py2.7"


def test_no_annotations_or_kwonly_args():
    bad = []
    for n in ast.walk(_tree()):
        if isinstance(n, ast.AnnAssign):
            bad.append("variable annotation")
        if isinstance(n, ast.arg) and n.annotation:
            bad.append("arg annotation: " + n.arg)
        if isinstance(n, ast.FunctionDef) and n.returns:
            bad.append("return annotation: " + n.name)
        if isinstance(n, ast.arguments) and n.kwonlyargs:
            bad.append("keyword-only args")
    assert bad == [], bad
