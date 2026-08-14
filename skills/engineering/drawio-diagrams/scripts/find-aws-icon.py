#!/usr/bin/env python3
"""find-aws-icon.py — look up official draw.io AWS icon styles by service name.

Searches references/aws-icons.md (the bundled catalogue) so the whole file never
has to be loaded into context. Prints each matching service name, its
mxgraph.aws4 icon id, and a ready-to-paste style string — resourceIcon for
services, group/grIcon for group containers (AWS Cloud, VPC, subnets, ...).

Usage
-----
  python3 find-aws-icon.py <query>      # e.g. ec2, lambda, s3, vpc

Lookup idea from softaworks/agent-toolkit's draw-io skill (MIT); reimplemented.
"""
import re
import sys
from pathlib import Path


def load_icons():
    path = Path(__file__).resolve().parent.parent / "references" / "aws-icons.md"
    return re.findall(r"\|\s*([^|\n]+?)\s*\|\s*(mxgraph\.aws4\.[a-z0-9_]+)\s*\|",
                      path.read_text(encoding="utf-8"))


def style_for(icon):
    if icon.startswith("mxgraph.aws4.group_"):
        return f"shape=mxgraph.aws4.group;grIcon={icon};"
    return f"shape=mxgraph.aws4.resourceIcon;resIcon={icon};"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    query = " ".join(sys.argv[1:]).lower()
    hits = [(n, i) for n, i in load_icons() if query in n.lower() or query in i]
    if not hits:
        print(f"No icons found for: {query}")
        return 1
    for name, icon in hits:
        print(f"{name}\n  icon:  {icon}\n  style: {style_for(icon)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
