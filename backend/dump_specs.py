import json
import yaml
from pathlib import Path

spec_dir = Path(__file__).resolve().parent.parent / "ml" / "specifications"
all_specs = {}

for p in sorted(spec_dir.glob("*.yaml")):
    if p.stem in ("dataset_registry", "schema-version"):
        continue
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    all_specs[p.stem] = {
        "disease_id": p.stem,
        "name": p.stem.replace("_", " ").title() if p.stem != "chronic_kidney_disease" else "Chronic Kidney Disease",
        "target": data.get("target", {}),
        "features": data.get("features", []),
        "disclaimer": data.get("disclaimer", ""),
    }

out_file = Path(__file__).resolve().parent / "all_disease_specs.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(all_specs, f, indent=2)

print(f"Exported {len(all_specs)} specs to {out_file}")
