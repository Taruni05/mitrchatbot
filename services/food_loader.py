"""
Food Data Loader - FIXED for nested structure
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
    
    UPDATED: Now handles nested structure like:
    {
      "restaurants": {
        "Heritage_Regional": [...],
        "Fine_Dining": [...],
        ...
      }
    }
    
    Returns:
        list: All restaurants with flattened data
    """
    logger.debug("Flattening restaurant data")
    restaurants = load_restaurant_data()

    # Check if restaurants is None or empty
    if not restaurants:
        logger.error("No restaurant data available")
        return []

    all_restaurants = []

    # NEW: Check if restaurants is a dict with categories
    if isinstance(restaurants, dict):
        logger.debug("Processing dict structure (categories)")
        
        # Iterate through categories (Heritage_Regional, Fine_Dining, etc.)
        for category, items in restaurants.items():
            if not isinstance(items, list):
                logger.warning(f"Category '{category}' is not a list, skipping")
                continue
            
            logger.debug(f"Processing category '{category}' with {len(items)} restaurants")
            
            for r in items:
                # Extract main branch location
                main_branch = r.get("main_branch", {})
                location = main_branch.get("location", "Hyderabad")
                maps_link = main_branch.get("google_maps_link", "")
                
                # Extract price range
                price_range_obj = r.get("price_range", {})
                if isinstance(price_range_obj, dict):
                    price_min = price_range_obj.get("min", 0)
                    price_max = price_range_obj.get("max", 0)
                    price_range = f"₹{price_min}-{price_max}"
                else:
                    price_range = "Check menu"
                
                # Extract opening hours (format as string)
                opening_hours_obj = r.get("opening_hours", {})
                if isinstance(opening_hours_obj, dict):
                    # Use Monday's hours as representative
                    opening_hours = opening_hours_obj.get("Monday", "11:00 AM - 11:00 PM")
                else:
                    opening_hours = "Check with restaurant"
                
                # Extract best selling dishes
                dishes = r.get("best_selling_dishes", [])
                # Clean up dishes - extract just the dish name before the colon
                clean_dishes = []
                for dish in dishes:
                    if isinstance(dish, str):
                        # Extract dish name (before colon)
                        dish_name = dish.split(":")[0].strip()
                        clean_dishes.append(dish_name)
                
                all_restaurants.append({
                    "name": r.get("name"),
                    "price_range": price_range,
                    "opening_hours": opening_hours,
                    "best_selling_dishes": clean_dishes,
                    "maps_link": maps_link,
                    "location": location,
                    "category": category
                })

    # OLD: Legacy support for flat list structure
    elif isinstance(restaurants, list):
        logger.debug("Processing list structure (legacy)")
        for r in restaurants:
            all_restaurants.append({
                "name": r.get("name"),
                "price_range": r.get("price_range"),
                "opening_hours": r.get("opening_hours"),
                "best_selling_dishes": r.get("best_selling_dishes"),
                "maps_link": r.get("maps_link"),
                "category": r.get("category", "General")
            })
    
    else:
        logger.error(f"Unexpected restaurants structure type: {type(restaurants)}")
        return []

    logger.info(f"✅ Flattened {len(all_restaurants)} total restaurants")
    return all_restaurants