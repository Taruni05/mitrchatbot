"""
Food Data Loader - Migrated with logging
Loads and processes restaurant data from knowledge base
"""

import json
from pathlib import Path
from services.kb_loader import get_restaurants
from services.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def load_restaurant_data():
    """Load restaurant data from knowledge base."""
    logger.debug("Loading restaurant data from knowledge base")
    restaurants = get_restaurants()
    
    if restaurants:
        logger.info(f"✅ Loaded {len(restaurants)} restaurant categories")
    else:
        logger.warning("No restaurant data found in knowledge base")
    
    return restaurants


def load_restaurants():
    """
    Load and flatten all restaurant data into a single list.
    
    Returns:
        list: All restaurants with flattened data
    """
    logger.debug("Flattening restaurant data")
    restaurants = load_restaurant_data()

    # Flatten all restaurant categories into one list
    all_restaurants = []

    for category, items in restaurants.items():
        logger.debug(f"Processing category '{category}' with {len(items)} restaurants")
        for r in items:
            all_restaurants.append({
                "name": r.get("name"),
                "price_range": r.get("price_range"),
                "opening_hours": r.get("opening_hours"),
                "best_selling_dishes": r.get("best_selling_dishes"),
                "maps_link": r.get("main_branch", {}).get("google_maps_link"),
                "category": category
            })

    logger.info(f"✅ Flattened {len(all_restaurants)} total restaurants")
    return all_restaurants