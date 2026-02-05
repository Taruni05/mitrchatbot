import json
from pathlib import Path
from services.kb_loader import get_restaurants

def load_restaurant_data():
    return get_restaurants()

def load_restaurants():
    restaurants=load_restaurant_data()

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

