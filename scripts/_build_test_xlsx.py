from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook


def main() -> None:
    out = Path(sys.argv[1])
    kind = sys.argv[2]

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["period", "category", "sum"])

    if kind == "valid":
        ws.append([date(2027, 1, 1), "видача", 9000])
        ws.append([date(2027, 1, 1), "збір", 3000])
    elif kind == "bad_period":
        ws.append([date(2027, 2, 15), "видача", 100])
    else:
        raise SystemExit(f"unknown kind: {kind}")

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)


if __name__ == "__main__":
    main()
