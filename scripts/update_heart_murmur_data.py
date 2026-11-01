"""Remove the retired duplicate heart-murmur compilation; keep earlier focused groups."""
import json
from pathlib import Path

DATA = Path("src/data/med-data.json")
RETIRED_IDS = {f"p83-g{i}" for i in range(5, 12)}

def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    original = len(payload["groups"])
    payload["groups"] = [g for g in payload["groups"] if g["id"] not in RETIRED_IDS]
    if len(payload["groups"]) != original:
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Removed {original - len(payload['groups'])} retired duplicate groups")

if __name__ == "__main__":
    main()
