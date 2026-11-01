"""CI check (no warehouse): every shipped CSV in presentation/data/ has the attribution line first and the columns the
page's SQL relies on, and the export script's writer produces the same shape. Run: python presentation/check_data.py"""
import csv
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import export_marts  # noqa: E402

DATA = pathlib.Path(__file__).parent / "data"
errors = []

for mart, columns in export_marts.EXPORTS.items():
    path = DATA / f"{mart}.csv"
    if not path.exists():
        errors.append(f"{path.name}: missing")
        continue
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines[0].startswith("#") or not any(k in lines[0] for k in ("CC BY-SA", "PLACEHOLDER")):
        errors.append(f"{path.name}: first line must be the attribution (or PLACEHOLDER) comment")
    header = next(csv.reader([lines[1]]))
    missing = [c for c in columns if c not in header]
    if missing:
        errors.append(f"{path.name}: missing columns {missing}")
    if len(lines) < 3:
        errors.append(f"{path.name}: no data rows")

# the writer round-trips: attribution line, header, rows
with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp) / "t.csv"
    export_marts.write_csv(out, ["a", "b"], [[1, "x,y"]], export_marts.attribution_line("2026-11-03"))
    got = out.read_text(encoding="utf-8").splitlines()
    if "CC BY-SA 4.0" not in got[0] or got[1] != "a,b" or got[2] != '1,"x,y"':
        errors.append(f"export_marts.write_csv output unexpected: {got}")

print("\n".join(errors) if errors else "presentation data checks passed")
sys.exit(1 if errors else 0)
