# Warehouse Manual Automation

Keeps **FG_Order_Tracker Main → Critical Item** columns live from Foodics:

| Column | Source |
|--------|--------|
| Warehouse Stock | Inventory Levels (`group_by=branch`) — **Main Warehouse `W01` only** |
| Branch Stock | Same report — sum of `B01`–`B08` |
| Total Stock | Warehouse + Branch (excludes Production `W02` / Head Office `W03`) |
| Daily Network Demand | Inventory Control → `consumption_from_order_quantity` **last 10 days ÷ 10** |

All other columns / sheets stay untouched.

## Rule

Local working tree must stay clean: every change is committed and pushed to  
https://github.com/firoz-ali45/Warehouse-Manual-Automation

## Sync (Cursor + Foodics MCP)

1. Agent pulls inventory levels + inventory control for Critical Item SKUs via Foodics MCP.
2. `python scripts/compute_critical_updates.py` writes:
   - `data/critical_updates.json`
   - `data/paste_DG.tsv` (59 rows → paste into **D3:G** on Critical Item)
3. Paste `data/paste_DG.tsv` into cell **D3** (Critical Item only).

## Sheet

https://docs.google.com/spreadsheets/d/1QkPRAVel7yEBc-fiwdiPbBu8UI7vhf9v1yjydlv3xsY/edit?gid=972439363
