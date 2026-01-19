import json
from pathlib import Path

def load_restaurants():
    base_path = Path(__file__).resolve().parent.parent
    kb_path = base_path / "knowledge_base.json"

    with open(kb_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    restaurants = data.get("restaurants", {})

    # Flatten all restaurant categories into one list
    all_restaurants = []

    for category, items in restaurants.items():
        for r in items:
            all_restaurants.append({
                "name": r.get("name"),
                "price_range": r.get("price_range"),
                "opening_hours": r.get("opening_hours"),
                "best_selling_dishes": r.get("best_selling_dishes"),
                "maps_link": r.get("main_branch", {}).get("google_maps_link"),
                "category": category
            })

    return all_restaurants
