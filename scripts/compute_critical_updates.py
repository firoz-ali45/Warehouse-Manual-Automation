"""
Compute Critical Item stock + Daily Network Demand from Foodics report dumps.

Rules (match existing FG_Order_Tracker sheet):
  - Warehouse Stock = Main Warehouse only (branch_reference W01)
  - Branch Stock    = sum of retail branches (B01–B08)
  - Total Stock     = Warehouse + Branch  (excludes W02 Production, W03 Head Office)
  - Daily Network Demand = sum(consumption_from_order_quantity over last 10 days) / 10
    across all locations for that item
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _clean(v: float):
    if abs(v - round(v)) < 1e-9:
        return int(round(v))
    return round(v, 5)


def compute(
    levels: list[dict],
    control: list[dict],
    sku_ids: dict[str, str],
    demand_days: int = 10,
) -> dict[str, dict]:
    id_to_sku = {uuid: sku for sku, uuid in sku_ids.items()}
    stock: dict[str, dict[str, float]] = defaultdict(
        lambda: {"warehouse_stock": 0.0, "branch_stock": 0.0}
    )

    for row in levels:
        sku = row.get("sku") or id_to_sku.get(row.get("inventory_item_id"))
        if not sku:
            continue
        ref = (row.get("branch_reference") or "").strip()
        qty = _num(row.get("quantity"))
        if ref == "W01":
            stock[sku]["warehouse_stock"] += qty
        elif ref.startswith("B"):
            stock[sku]["branch_stock"] += qty

    consumption: dict[str, float] = defaultdict(float)
    for row in control:
        iid = row.get("inventory_item_id") or row.get("item_id")
        sku = row.get("sku") or id_to_sku.get(iid)
        if not sku:
            continue
        consumption[sku] += _num(row.get("consumption_from_order_quantity"))

    updates: dict[str, dict] = {}
    for sku in sku_ids:
        w = stock[sku]["warehouse_stock"]
        b = stock[sku]["branch_stock"]
        demand = consumption[sku] / float(demand_days)
        updates[sku] = {
            "warehouse_stock": _clean(w),
            "branch_stock": _clean(b),
            "total_stock": _clean(w + b),
            "daily_network_demand": round(demand, 4),
        }
    return updates


def build_paste_tsv(updates: dict[str, dict], sheet_tsv: Path) -> str:
    lines = sheet_tsv.read_text(encoding="utf-8-sig").splitlines()
    skus: list[str] = []
    for line in lines[2:]:
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip().startswith("sk-"):
            skus.append(parts[1].strip())

    def fmt(n) -> str:
        if isinstance(n, float):
            return f"{n:.5f}".rstrip("0").rstrip(".")
        return str(n)

    rows = []
    for sku in skus:
        u = updates[sku]
        rows.append(
            "\t".join(
                fmt(u[k])
                for k in (
                    "warehouse_stock",
                    "branch_stock",
                    "total_stock",
                    "daily_network_demand",
                )
            )
        )
    return "\n".join(rows)


def main() -> None:
    levels = json.loads((DATA / "inventory_levels_raw.json").read_text(encoding="utf-8"))
    control = json.loads((DATA / "inventory_control_raw.json").read_text(encoding="utf-8"))
    sku_ids = json.loads((DATA / "sku_ids.json").read_text(encoding="utf-8"))
    updates = compute(levels, control, sku_ids)
    (DATA / "critical_updates.json").write_text(
        json.dumps(updates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paste = build_paste_tsv(updates, ROOT / "critical_items_sheet.tsv")
    (DATA / "paste_DG.tsv").write_text(paste + "\n", encoding="utf-8")
    print(f"Wrote {len(updates)} SKU updates → data/critical_updates.json")
    print(f"Paste block ({len(paste.splitlines())} rows) → data/paste_DG.tsv")


if __name__ == "__main__":
    main()
