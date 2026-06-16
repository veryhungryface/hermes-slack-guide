#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$")


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter delimited by ---")

    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        values[key.strip()] = value
    return values


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Skill path does not exist: {path}"]
    if not path.is_dir():
        return [f"Skill path must be a directory: {path}"]

    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return [f"Missing required file: {skill_md}"]

    try:
        frontmatter = parse_frontmatter(skill_md)
    except Exception as exc:
        return [str(exc)]

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not name:
        errors.append("Frontmatter is missing required field: name")
    elif not NAME_RE.fullmatch(name):
        errors.append("Skill name must use lowercase letters, digits, and hyphens only")
    elif path.name != name:
        errors.append(f"Skill folder name must match frontmatter name: {path.name} != {name}")

    if not description:
        errors.append("Frontmatter is missing required field: description")
    elif len(description) < 24:
        errors.append("Description is too short to be useful")

    agents_yaml = path / "agents" / "openai.yaml"
    if agents_yaml.exists():
        text = agents_yaml.read_text(encoding="utf-8")
        for needle in ("display_name:", "short_description:", "default_prompt:"):
            if needle not in text:
                errors.append(f"agents/openai.yaml is missing {needle}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Codex skill folder.")
    parser.add_argument("skill_path", type=Path, help="Path to the skill folder")
    args = parser.parse_args()

    errors = validate_skill(args.skill_path.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Skill is valid!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
