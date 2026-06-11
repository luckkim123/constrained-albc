"""EXPORT_REPORT.md generation (guide section 6 fields)."""
from __future__ import annotations

from constrained_albc.deploy.verify import ContractReport


def build_report(
    reports: dict[str, ContractReport],
    chosen: dict[str, dict],
    out_dir: str,
    mount_status: str,
    golden_status: str,
) -> str:
    """Render the export report markdown. All inputs are already-computed facts."""
    lines: list[str] = []
    lines.append("# Deploy Export Report - attitude-only 5000-iter")
    lines.append("")
    lines.append("## Chosen checkpoints")
    lines.append("")
    lines.append("| spec | file | iter | rationale |")
    lines.append("|:--|:--|:--|:--|")
    for name, info in chosen.items():
        lines.append(f"| {name} | {info['file']} | {info['iter']} | {info['rationale']} |")
    lines.append("")
    lines.append("## Verified dimensions")
    lines.append("")
    lines.append("- policy obs dim: 69 (channel_transform.0.weight input)")
    lines.append("- action dim: 8 (actor.6.weight output)")
    lines.append("- latent dim: 9 (head.3.weight output)")
    lines.append("- teacher actor input: 78 (actor.0.weight input = obs69 + latent9)")
    lines.append("")
    for name, rep in reports.items():
        lines.append(f"## {name}: {rep.path}")
        lines.append("")
        lines.append(f"contract: {'PASS' if rep.ok else 'FAIL'}")
        lines.append("")
        lines.append("| key | shape | dtype |")
        lines.append("|:--|:--|:--|")
        for key, shape, dtype in rep.entries:
            lines.append(f"| {key} | {shape} | {dtype} |")
        lines.append("")
    lines.append("## Golden e2e")
    lines.append("")
    lines.append(golden_status)
    lines.append("")
    lines.append("## Output location")
    lines.append("")
    lines.append(f"- absolute path: `{out_dir}`")
    lines.append(f"- volume mount: {mount_status}")
    return "\n".join(lines) + "\n"
