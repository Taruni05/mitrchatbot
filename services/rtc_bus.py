import pandas as pd
import streamlit as st
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from services.logger import get_logger
from services.config import config

# Initialize logger
logger = get_logger(__name__)


# Load CSV data
@st.cache_data


def load_rtc_routes():
    """Load RTC routes from CSV file"""
    try:
        csv_path = Path(__file__).resolve().parent.parent / "data" / "rtc_routes.csv"
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        st.error(f"Error loading RTC routes: {e}")
        return pd.DataFrame()  # Return empty dataframe on error


# Area name normalization
AREA_ALIASES = {
    "hitech": "hitec city",
    "hi-tech": "hitec city",
    "hi tech": "hitec city",
    "cyber towers": "hitec city",
    "cyberabad": "hitec city",
    "sec bad": "secunderabad",
    "secbad": "secunderabad",
    "secundrabad": "secunderabad",
    "lb nagar": "lb nagar",
    "lbnagar": "lb nagar",
    "dilsukh nagar": "dilsukhnagar",
    "kphb": "kukatpally",
    "jubs": "jubilee hills",
    "jub hills": "jubilee hills",
    "old city": "charminar",
    "gachi": "gachibowli",
    "madhapur": "madhapur",
    "mehdipatnam": "mehdipatnam",
    "tolichowki": "tolichowki",
    "miyapur": "miyapur",
    "uppal": "uppal"
}


def normalize_area(area: str) -> str:
    """Normalize area names to match database"""
    area_lower = area.lower().strip()
    
    # Direct match
    if area_lower in AREA_ALIASES:
        return AREA_ALIASES[area_lower]
    
    # Return as-is (will match CSV if exact)
    return area_lower


def extract_locations_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract 'from' and 'to' locations from user query.
    
    Examples:
        "Bus from Ameerpet to HITEC City" → ("ameerpet", "hitec city")
        "How to reach Charminar from Secunderabad" → ("secunderabad", "charminar")
    
    Returns:
        (from_location, to_location) or (None, None)
    """
    query_lower = query.lower()
    
    # Pattern 1: "from X to Y"
    if "from" in query_lower and "to" in query_lower:
        parts = query_lower.split("from")[1].split("to")
        if len(parts) == 2:
            from_area = normalize_area(parts[0].strip())
            to_area = normalize_area(parts[1].strip())
            return from_area, to_area
    
    # Pattern 2: "reach X from Y" or "go to X from Y"
    if "reach" in query_lower or "go to" in query_lower:
        if "from" in query_lower:
            if "reach" in query_lower:
                parts = query_lower.split("reach")[1].split("from")
            else:
                parts = query_lower.split("go to")[1].split("from")
            
            if len(parts) == 2:
                to_area = normalize_area(parts[0].strip())
                from_area = normalize_area(parts[1].strip())
                return from_area, to_area
    
    # Pattern 3: "to X" (assume user is asking from current/popular location)
    if "to" in query_lower and "from" not in query_lower:
        parts = query_lower.split("to")
        if len(parts) >= 2:
            to_area = normalize_area(parts[1].strip())
            return None, to_area  # Will show all routes to destination
    
    return None, None


def get_bus_routes(from_area: str, to_area: str) -> pd.DataFrame:
    """
    Get bus routes between two areas from CSV.
    
    Args:
        from_area: Starting location (normalized)
        to_area: Destination (normalized)
    
    Returns:
        DataFrame of matching routes or empty DataFrame
    """
    df = load_rtc_routes()
    
    if df.empty:
        return df
    
    # Normalize CSV data for comparison (CRITICAL FIX)
    df['from_area_norm'] = df['from_area'].str.lower().str.strip()
    df['to_area_norm'] = df['to_area'].str.lower().str.strip()
    
    # Also normalize the search terms to lowercase
    from_area_search = from_area.lower().strip() if from_area else None
    to_area_search = to_area.lower().strip() if to_area else None
    
    # Filter routes
    if from_area_search and to_area_search:
        # Specific route query
        routes = df[
            (df['from_area_norm'] == from_area_search) & 
            (df['to_area_norm'] == to_area_search)
        ]
        
        # If no results, try reverse direction
        if routes.empty:
            routes = df[
                (df['from_area_norm'] == to_area_search) & 
                (df['to_area_norm'] == from_area_search)
            ]
            
            # If found reverse routes, add a note
            if not routes.empty:
                routes = routes.copy()
                routes['reverse_route'] = True
    
    elif to_area_search:
        # Only destination specified (show all routes to that area)
        routes = df[df['to_area_norm'] == to_area_search].head(5)
    
    else:
        routes = pd.DataFrame()
    
    return routes


def find_common_hubs(from_area: str, to_area: str) -> List[str]:
    """
    Find potential hub stations for connecting routes.
    Returns list of hubs sorted by connectivity.
    """
    # Major interchange hubs in Hyderabad (sorted by importance)
    MAJOR_HUBS = [
        "ameerpet",          # Central hub
        "secunderabad",      # Railway & bus hub
        "kukatpally",        # Western hub
        "dilsukhnagar",      # Eastern hub
        "mehdipatnam",       # Southern hub
        "lakdikapul",        # Central business
        "koti",              # Old city gateway
        "jubilee hills",     # Residential hub
        "gachibowli",        # IT hub
        "lb nagar",          # Southern terminus
        "uppal",             # Eastern hub
    ]
    
    df = load_rtc_routes()
    if df.empty:
        return []
    
    # Normalize
    df['from_area_norm'] = df['from_area'].str.lower().str.strip()
    df['to_area_norm'] = df['to_area'].str.lower().str.strip()
    
    from_area_norm = from_area.lower().strip()
    to_area_norm = to_area.lower().strip()
    
    # Find hubs that connect to both areas
    valid_hubs = []
    
    for hub in MAJOR_HUBS:
        # Skip if hub is same as origin or destination
        if hub == from_area_norm or hub == to_area_norm:
            continue
        
        # Check if there are routes: from_area → hub
        leg1_exists = not df[
            ((df['from_area_norm'] == from_area_norm) & (df['to_area_norm'] == hub)) |
            ((df['from_area_norm'] == hub) & (df['to_area_norm'] == from_area_norm))
        ].empty
        
        # Check if there are routes: hub → to_area
        leg2_exists = not df[
            ((df['from_area_norm'] == hub) & (df['to_area_norm'] == to_area_norm)) |
            ((df['from_area_norm'] == to_area_norm) & (df['to_area_norm'] == hub))
        ].empty
        
        if leg1_exists and leg2_exists:
            valid_hubs.append(hub)
    
    # Return top 3 hubs
    return valid_hubs[:3]


def get_connecting_routes(from_area: str, to_area: str) -> List[Dict]:
    """
    Find multi-hop routes with 1 connection.
    
    Returns:
        List of connection options, each containing:
        {
            'hub': str,
            'leg1': DataFrame,
            'leg2': DataFrame,
            'total_time': int,
            'total_fare_min': int,
            'total_fare_max': int
        }
    """
    hubs = find_common_hubs(from_area, to_area)
    
    if not hubs:
        return []
    
    connections = []
    
    for hub in hubs:
        # Get routes for leg 1
        leg1_routes = get_bus_routes(from_area, hub)
        
        # Get routes for leg 2
        leg2_routes = get_bus_routes(hub, to_area)
        
        if not leg1_routes.empty and not leg2_routes.empty:
            # Calculate total journey metrics
            if leg1_routes.empty or leg2_routes.empty:

                logger.warning(f"Empty routes found for hub {hub}")

                continue

            

            leg1_time = leg1_routes.iloc[0]['duration_mins']
            leg2_time = leg2_routes.iloc[0]['duration_mins']
            
            # Add connection time (5-10 mins based on hub size)
            connection_time = 10 if hub in ['secunderabad', 'ameerpet'] else 5
            
            total_time = leg1_time + leg2_time + connection_time
            
            # Calculate fare range
            leg1_fare_min = leg1_routes.iloc[0]['fare_min']
            leg1_fare_max = leg1_routes.iloc[0]['fare_max']
            leg2_fare_min = leg2_routes.iloc[0]['fare_min']
            leg2_fare_max = leg2_routes.iloc[0]['fare_max']
            
            total_fare_min = leg1_fare_min + leg2_fare_min
            total_fare_max = leg1_fare_max + leg2_fare_max
            
            connections.append({
                'hub': hub,
                'leg1': leg1_routes.head(3),  # Top 3 options for leg 1
                'leg2': leg2_routes.head(3),  # Top 3 options for leg 2
                'total_time': total_time,
                'total_fare_min': total_fare_min,
                'total_fare_max': total_fare_max,
                'connection_time': connection_time
            })
    
    # Sort by total time (fastest first)
    connections.sort(key=lambda x: x['total_time'])
    
    return connections


def format_connecting_routes(from_area: str, to_area: str, connections: List[Dict]) -> str:
    """
    Format connecting routes into readable response.
    """
    if not connections:
        return ""
    
    response = f"\n\n🔄 **CONNECTING ROUTES** (1 Change):\n\n"
    
    for idx, conn in enumerate(connections, 1):
        hub = conn['hub'].title()
        leg1 = conn['leg1']
        leg2 = conn['leg2']
        
        response += "━" * 45 + "\n"
        response += f"**Option {idx}: Via {hub}**"
        
        # Add "Fastest" badge to first option
        if idx == 1:
            response += " ⚡ *Fastest*"
        
        response += "\n"
        response += "━" * 45 + "\n\n"
        
        # Leg 1
        response += f"**Leg 1:** {from_area.title()} → {hub}\n"
        
        buses_leg1 = ", ".join(leg1['route_number'].head(3).tolist())
        if leg1.empty:

            logger.error("leg1 DataFrame is empty")

            continue

        avg_time_leg1 = leg1.iloc[0]['duration_mins']
        fare_min_leg1 = leg1.iloc[0]['fare_min']
        fare_max_leg1 = leg1.iloc[0]['fare_max']
        
        response += f"🔹 Bus {buses_leg1}  \n"
        response += f"   ⏱️ ~{avg_time_leg1} mins | 💰 ₹{fare_min_leg1}-{fare_max_leg1}\n\n"
        
        # Connection info
        response += f"🔄 **Change at {hub}**"
        if conn['connection_time'] >= 10:
            response += " (Major hub - allow 10 mins)"
        else:
            response += " (Walk ~2 mins to connecting stop)"
        response += "\n\n"
        
        # Leg 2
        response += f"**Leg 2:** {hub} → {to_area.title()}\n"
        
        buses_leg2 = ", ".join(leg2['route_number'].head(3).tolist())
        avg_time_leg2 = leg2.iloc[0]['duration_mins']
        fare_min_leg2 = leg2.iloc[0]['fare_min']
        fare_max_leg2 = leg2.iloc[0]['fare_max']
        
        response += f"🔹 Bus {buses_leg2}  \n"
        response += f"   ⏱️ ~{avg_time_leg2} mins | 💰 ₹{fare_min_leg2}-{fare_max_leg2}\n\n"
        
        # Summary
        response += "📊 **Total Journey:**  \n"
        response += f"⏱️ ~{conn['total_time']} mins (including {conn['connection_time']} min change)  \n"
        response += f"💰 Total Fare: ₹{conn['total_fare_min']}-{conn['total_fare_max']}  \n"
        response += f"🚏 1 change required\n\n"
    
    # Add recommendation
    if len(connections) > 1:
        fastest = connections[0]
        response += f"💡 **Recommendation:** Option 1 via {fastest['hub'].title()} is fastest!\n\n"
    
    return response


def format_bus_routes(from_area: str, to_area: str, routes: pd.DataFrame) -> str:
    """
    Format bus routes from CSV data into readable response.
    """
    if routes.empty:
        if from_area and to_area:
            return f"""🚌 **No direct bus routes found** from **{from_area.title()}** to **{to_area.title()}**.

💡 **Suggestions:**
- Take Metro if available (faster and more reliable)
- Use Google Maps for multi-hop bus routes
- Consider auto/cab for this journey
- Try major hubs like Ameerpet or Secunderabad for better connectivity

📱 Download **TSRTC App** for live bus tracking and more routes."""
        elif to_area:
            return f"""🚌 **No bus routes found to {to_area.title()}**.

Try asking with a starting point:
"Bus from Ameerpet to {to_area.title()}"

📱 Download **TSRTC App** for comprehensive route search."""
        else:
            return get_general_bus_info()
    
    # Check if these are reverse routes
    is_reverse = routes.iloc[0].get('reverse_route', False) if len(routes) > 0 else False
    
    # Build response
    if from_area and to_area:
        if is_reverse:
            response = f"🚌 **BUS ROUTES:** {to_area.title()} → {from_area.title()}\n"
            response += f"*(Showing reverse direction routes - board these buses from {to_area.title()})*\n\n"
        else:
            response = f"🚌 **BUS ROUTES:** {from_area.title()} → {to_area.title()}\n\n"
    else:
        response = f"🚌 **BUS ROUTES TO:** {to_area.title()}\n\n"
    
    for idx, row in routes.iterrows():
        route_num = row['route_number']
        
        # Handle reverse display
        if is_reverse:
            via = row['via_stops'].replace(',', ' → ')
            # Reverse the via stops
            via_parts = via.split(' → ')
            via = ' → '.join(reversed(via_parts))
            display_from = row['to_area']
            display_to = row['from_area']
        else:
            via = row['via_stops'].replace(',', ' → ')
            display_from = row['from_area']
            display_to = row['to_area']
        
        freq = row['frequency_mins']
        duration = row['duration_mins']
        fare_min = row['fare_min']
        fare_max = row['fare_max']
        service = row['service_type']
        first = row['first_bus']
        last = row['last_bus']
        
        # Calculate average frequency range
        freq_text = f"{freq}-{freq+5} mins" if freq < 30 else f"{freq} mins"
        
        response += f"🔹 **Bus {route_num}** ({service})  \n"
        response += f"   ⏱️ Frequency: Every {freq_text}  \n"
        response += f"   🕐 Duration: ~{duration} mins  \n"
        response += f"   💰 Fare: ₹{fare_min}-{fare_max}  \n"
        response += f"   📍 Via: {via}  \n"
        response += f"   🕐 Timings: {first} - {last}\n\n"
    
    response += """💡 **Tips:**  
- Buses are most frequent during 8-10 AM and 5-8 PM  
- Download **TSRTC App** for live bus tracking  
- Keep change ready (₹10, ₹20 notes)  
- Board from designated bus stops for safety

📱 **TSRTC App:** Track your bus in real-time!"""
    
    return response


def get_general_bus_info() -> str:
    """
    Return general RTC bus information.
    """
    df = load_rtc_routes()
    
    # Get some popular routes for display
    popular_routes = ""
    if not df.empty:
        # Group by route to show unique routes
        unique_routes = df.drop_duplicates(subset=['from_area', 'to_area']).head(6)
        
        for idx, row in unique_routes.iterrows():
            popular_routes += f"• {row['from_area']} ↔ {row['to_area']} (Bus {row['route_number']})\n"
    
    return f"""🚌 **TSRTC BUS SERVICES IN HYDERABAD**

**Major Bus Depots:**
- 🏢 JBS (Jubilee Bus Station) - Secunderabad
- 🏢 MGBS (Mahatma Gandhi Bus Station) - Old City
- 🏢 Dilsukhnagar Bus Depot
- 🏢 Kukatpally Bus Depot
- 🏢 Miyapur Bus Depot

**Popular Routes:**
{popular_routes if popular_routes else "• Loading route data..."}

**Timings:**
⏰ First Bus: 5:00 AM  
🌙 Last Bus: 11:30 PM  
⚡ Peak Hours: 8-10 AM, 5-8 PM

**Fares:**
💰 City Ordinary: ₹5-40 (based on distance)
💰 Metro Express: ₹20-60 (AC buses)

📱 **Download:** TSRTC app for live bus tracking

❓ **Ask me:** "Bus from [Area A] to [Area B]" for specific routes!

**Example queries:**
- "Bus from Ameerpet to HITEC City"
- "How to reach Charminar from Secunderabad?"
- "Buses to Gachibowli"""""


def get_route_statistics() -> Dict:
    """Get statistics about available routes"""
    df = load_rtc_routes()
    
    if df.empty:
        return {}
    
    return {
        "total_routes": len(df),
        "unique_buses": df['route_number'].nunique(),
        "areas_covered": len(set(df['from_area'].tolist() + df['to_area'].tolist()))
    }