"""
gen_examples.py

Scans packages/sayou-*/examples/quick_start_*.py and generates:
  - docs/examples/{lib}.md            (one page per library, all examples)
  - packages/sayou-{lib}/examples/{stem}.ipynb  (alongside each .py)

.py file conventions:
  Section header:  # ── Section Title
  Description:     triple-quoted string immediately after the header
  Code:            everything else until the next header

Usage:
  python scripts/gen_examples.py
"""

import json
import re
import textwrap
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
PACKAGES_DIR = ROOT / "packages"
DOCS_EXAMPLES_DIR = ROOT / "docs" / "examples" / "src"

SECTION_RE = re.compile(r"^# ──+\s*(.+?)\s*─*$")


def parse_py(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    sections = []
    current = None
    i = 0

    while i < len(lines):
        line = lines[i]
        m = SECTION_RE.match(line)
        if m:
            if current:
                sections.append(current)
            current = {"title": m.group(1), "description": "", "code": []}
            i += 1
            continue

        if current is None:
            i += 1
            continue

        if not current["code"] and line.strip().startswith('"""'):
            if line.count('"""') >= 2:
                inner = re.match(r'\s*"""(.*?)"""', line)
                if inner:
                    current["description"] = textwrap.dedent(inner.group(1)).strip()
            else:
                parts = [line.split('"""', 1)[1]]
                i += 1
                while i < len(lines):
                    if '"""' in lines[i]:
                        parts.append(lines[i].split('"""')[0])
                        break
                    parts.append(lines[i])
                    i += 1
                current["description"] = textwrap.dedent("\n".join(parts)).strip()
            i += 1
            continue

        current["code"].append(line)
        i += 1

    if current:
        sections.append(current)

    for s in sections:
        while s["code"] and not s["code"][-1].strip():
            s["code"].pop()

    return sections


def example_title(filename: str) -> str:
    """quick_start_code.py -> Quick Start Code"""
    return filename.replace(".py", "").replace("_", " ").title()


def write_md(lib: str, py_files: list[Path], out_path: Path):
    """
    No top-level # heading — title is provided externally
    (tab label or nav entry). Works unchanged in both layouts.
    """
    source_line = (
        f"    Synced from [`packages/sayou-{lib}/examples/{py_files[0].name}`]"
        f"(https://github.com/sayouzone/sayou-fabric/blob/main/"
        f"packages/sayou-{lib}/examples/{py_files[0].name})."
    )
    lines = [
        '!!! abstract "Source"',
        source_line,
        "",
    ]

    for py_file in py_files:
        sections = parse_py(py_file)
        if not sections:
            continue

        for s in sections:
            lines.append(f"## {s['title']}")
            lines.append("")
            if s["description"]:
                lines.append(s["description"])
                lines.append("")
            if s["code"]:
                code = "\n".join(s["code"]).strip()
                if code:
                    lines.append("```python")
                    lines.append(code)
                    lines.append("```")
                    lines.append("")

    while lines and not lines[-1]:
        lines.pop()

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_ipynb(lib: str, py_file: Path, sections: list[dict], out_path: Path):
    title = example_title(py_file.name)
    cells = []

    cells.append(
        {
            "cell_type": "markdown",
            "id": "title",
            "metadata": {},
            "source": [f"# {title}\n"],
        }
    )

    for idx, s in enumerate(sections):
        md_source = [f"## {s['title']}\n"]
        if s["description"]:
            md_source.append("\n")
            md_source.extend(l + "\n" for l in s["description"].splitlines())
        cells.append(
            {
                "cell_type": "markdown",
                "id": f"md-{idx}",
                "metadata": {},
                "source": md_source,
            }
        )

        if s["code"]:
            code = "\n".join(s["code"]).strip()
            if code:
                cells.append(
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "id": f"code-{idx}",
                        "metadata": {},
                        "outputs": [],
                        "source": [l + "\n" for l in code.splitlines()],
                    }
                )

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": cells,
    }
    out_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")


def lib_name(package_dir: Path) -> str:
    return package_dir.name.replace("sayou-", "")


def main():
    DOCS_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    # Group .py files by library
    lib_files: dict[str, list[Path]] = defaultdict(list)
    for py_file in sorted(PACKAGES_DIR.glob("sayou-*/examples/quick_start_*.py")):
        lib = lib_name(py_file.parent.parent)
        lib_files[lib].append(py_file)

    if not lib_files:
        print("No quick_start_*.py files found.")
        return

    for lib, py_files in sorted(lib_files.items()):
        for py_file in py_files:
            sections = parse_py(py_file)
            if not sections:
                print(f"  ⚠  No sections in {py_file.name}, skipping.")
                continue

            # One .md per .py — dumped into docs/examples/src/
            md_path = DOCS_EXAMPLES_DIR / f"{lib}_{py_file.stem}.md"
            write_md(lib, [py_file], md_path)
            print(f"  ✓ md    → {md_path.relative_to(ROOT)}")

            # .ipynb alongside the .py
            ipynb_path = py_file.with_suffix(".ipynb")
            write_ipynb(lib, py_file, sections, ipynb_path)
            print(f"  ✓ ipynb → {ipynb_path.relative_to(ROOT)}")

    print("\nDone.")
    print("Place generated md files into mkdocs.yml nav however you like.")


if __name__ == "__main__":
    main()
