#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    return subprocess.call([sys.executable, "-m", "uvicorn", "api.main:app", "--reload"])


if __name__ == "__main__":
    raise SystemExit(main())
