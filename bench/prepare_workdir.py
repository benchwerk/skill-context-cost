#!/usr/bin/env python3
"""Build the working directory of one configuration, exactly as run.py does, and print its path.

Usage: python bench/prepare_workdir.py C50
Then open Claude Code there for screen footage (with the isolated CLAUDE_CONFIG_DIR set) and type /context.
The directory is the fixed path from config.json (workdir_root\\w), recreated on every call."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in run.MAN["sets"]:
        sys.exit(__doc__ + "\nconfigurations: " + ", ".join(run.MAN["sets"]))
    print(run.build_workdir(sys.argv[1]))


if __name__ == "__main__":
    main()
