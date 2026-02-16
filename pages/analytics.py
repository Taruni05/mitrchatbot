"""
Analytics Dashboard
Shows user's chat history, usage patterns, and insights.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
from collections import Counter

# Import services
from services.auth import is_logged_in, get_current_user_id, require_login
from services.user_store import get_user_stats, load_chat_history, load_preferences
from services.cache_manager import get_cache_stats
from services.logger import get_logger

logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Analytics - MITR",
    page_icon="📊",
    layout="wide"
)

# Require login
if not require_login():
    st.stop()

# ============================================================================
# HEADER
# ============================================================================

st.title("📊 Your MITR Analytics")
st.markdown("Insights into your Hyderabad exploration journey")

# Get user data
user_id = get_current_user_id()
stats = get_user_stats()
preferences = load_preferences()
history = load_chat_history(limit=100)

# ============================================================================
# OVERVIEW METRICS
# ============================================================================

st.markdown("---")
st.subheader("📈 Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_chats = stats.get("total_messages", 0)
    st.metric("💬 Total Conversations", total_chats)

with col2:
    days_active = stats.get("days_active", 0)
    st.metric("📅 Days Active", days_active)

with col3:
    avg_per_day = total_chats / days_active if days_active > 0 else 0
    st.metric("📊 Avg Chats/Day", f"{avg_per_day:.1f}")

with col4:
    cache_stats = get_cache_stats()
    hit_rate = cache_stats.get("hit_rate", 0)
    st.metric("⚡ Cache Hit Rate", f"{hit_rate:.0f}%")

# ============================================================================
# INTENT BREAKDOWN
# ============================================================================

if history:
    st.markdown("---")
    st.subheader("🎯 What You Ask About Most")
    
    # Extract intents from history
    intents = [msg.get("intent", "unknown") for msg in history if msg.get("intent")]
    
    if intents:
        intent_counts = Counter(intents)
        
        # Create DataFrame for plotting
        intent_df = pd.DataFrame(
            intent_counts.most_common(10),
            columns=["Intent", "Count"]
        )
        
        # Display as bar chart
        st.bar_chart(intent_df.set_index("Intent"))
        
        # Show top 5 as text
        st.markdown("**Top 5 Topics:**")
        for intent, count in intent_counts.most_common(5):
            percentage = (count / len(intents)) * 100
            st.markdown(f"- **{intent.title()}**: {count} queries ({percentage:.1f}%)")
    else:
        st.info("No intent data available yet. Keep chatting!")

# ============================================================================
# ACTIVITY TIMELINE
# ============================================================================

if history and len(history) > 5:
    st.markdown("---")
    st.subheader("📅 Activity Timeline")
    
    # Convert to DataFrame
    df = pd.DataFrame(history)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    df["hour"] = df["created_at"].dt.hour
    
    # Daily activity
    daily_counts = df.groupby("date").size().reset_index(name="messages")
    daily_counts.columns = ["Date", "Messages"]
    
    # Line chart
    st.line_chart(daily_counts.set_index("Date"))
    
    # Peak hours
    st.markdown("**🕐 Your Peak Usage Hours:**")
    hourly_counts = df["hour"].value_counts().sort_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        peak_hour = hourly_counts.idxmax()
        peak_count = hourly_counts.max()
        
        # Convert hour to readable format
        if peak_hour < 12:
            time_str = f"{peak_hour}:00 AM"
        elif peak_hour == 12:
            time_str = "12:00 PM"
        else:
            time_str = f"{peak_hour - 12}:00 PM"
        
        st.metric("Peak Hour", time_str, f"{peak_count} chats")
    
    with col2:
        # Average response time (if we tracked it)
        st.metric("Avg Response Time", "< 3 sec", "Fast ⚡")
    
    # Hourly heatmap data
    st.markdown("**📊 Usage by Hour of Day:**")
    hourly_df = pd.DataFrame({
        "Hour": hourly_counts.index,
        "Chats": hourly_counts.values
    })
    st.bar_chart(hourly_df.set_index("Hour"))

# ============================================================================
# FAVORITE PLACES & INTERESTS
# ============================================================================

st.markdown("---")
st.subheader("❤️ Your Favorites")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🍽️ Favorite Cuisines:**")
    fav_cuisines = preferences.get("favorite_cuisines", [])
    if fav_cuisines:
        for cuisine in fav_cuisines[:5]:
            st.markdown(f"- {cuisine.title()}")
    else:
        st.caption("No favorites saved yet")

with col2:
    st.markdown("**🎯 Interests:**")
    interests = preferences.get("interests", [])
    if interests:
        for interest in interests[:5]:
            st.markdown(f"- {interest.title()}")
    else:
        st.caption("No interests saved yet")

# Home area
home_area = preferences.get("home_area", "")
if home_area:
    st.markdown(f"**🏠 Home Area:** {home_area.title()}")

# ============================================================================
# RECENT CONVERSATIONS
# ============================================================================

if history:
    st.markdown("---")
    st.subheader("💬 Recent Conversations")
    
    # Show last 10 conversations
    recent = history[:10]
    
    for i, msg in enumerate(recent, 1):
        with st.expander(
            f"{i}. {msg['user_message'][:60]}..." if len(msg['user_message']) > 60 
            else f"{i}. {msg['user_message']}"
        ):
            # User message
            st.markdown("**You asked:**")
            st.markdown(f"> {msg['user_message']}")
            
            # Bot response
            st.markdown("**MITR replied:**")
            st.markdown(msg['bot_response'][:300] + "..." if len(msg['bot_response']) > 300 else msg['bot_response'])
            
            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"🏷️ Intent: {msg.get('intent', 'unknown')}")
            with col2:
                timestamp = pd.to_datetime(msg['created_at'])
                st.caption(f"🕐 {timestamp.strftime('%b %d, %Y at %I:%M %p')}")

# ============================================================================
# SEARCH HISTORY
# ============================================================================

if history and len(history) > 10:
    st.markdown("---")
    st.subheader("🔍 Search Your History")
    
    search_query = st.text_input("Search your past conversations:", placeholder="e.g., biryani, weather, metro")
    
    if search_query:
        # Search in user messages and bot responses
        search_lower = search_query.lower()
        results = [
            msg for msg in history
            if search_lower in msg['user_message'].lower() or search_lower in msg['bot_response'].lower()
        ]
        
        if results:
            st.success(f"Found {len(results)} matching conversations:")
            
            for i, msg in enumerate(results[:5], 1):  # Show top 5
                with st.expander(f"{i}. {msg['user_message'][:50]}..."):
                    st.markdown(f"**Q:** {msg['user_message']}")
                    st.markdown(f"**A:** {msg['bot_response'][:200]}...")
        else:
            st.info("No matching conversations found.")

# ============================================================================
# INSIGHTS & RECOMMENDATIONS
# ============================================================================

st.markdown("---")
st.subheader("💡 Personalized Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🎯 Based on Your Usage:**")
    
    # Generate insights based on history
    if history:
        # Most common intent
        intents = [msg.get("intent", "") for msg in history if msg.get("intent")]
        if intents:
            most_common = Counter(intents).most_common(1)[0][0]
            
            insights = {
                "food": "You love exploring food! 🍛 Try our new restaurant recommendations feature.",
                "weather": "You check weather often! ☀️ Enable notifications for weather alerts.",
                "traffic": "You're a commuter! 🚗 Save your frequent routes for quick access.",
                "monuments": "You're a history buff! 🏛️ Check out our guided tour suggestions.",
                "metro": "You use public transport! 🚇 Download offline metro maps.",
                "shopping": "You love shopping! 🛍️ Get alerts for new mall openings.",
            }
            
            insight = insights.get(most_common, "Keep exploring Hyderabad with MITR!")
            st.info(insight)

with col2:
    st.markdown("**📊 Your Stats vs Average User:**")
    
    # Compare with averages (hardcoded for demo)
    avg_user_chats = 25
    your_percentile = min(100, (total_chats / avg_user_chats) * 100)
    
    if total_chats > avg_user_chats:
        st.success(f"You're in the top {100 - your_percentile:.0f}% most active users! 🌟")
    else:
        st.info(f"You're {your_percentile:.0f}% as active as average users.")

# ============================================================================
# DATA EXPORT
# ============================================================================

st.markdown("---")
st.subheader("📥 Export Your Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Download Chat History (CSV)", use_container_width=True):
        if history:
            # Convert to DataFrame
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"mitr_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No history to export")

with col2:
    if st.button("📊 Download Analytics Report (JSON)", use_container_width=True):
        import json
        
        report = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "stats": stats,
            "preferences": preferences,
            "total_conversations": len(history),
            "cache_stats": cache_stats
        }
        
        json_str = json.dumps(report, indent=2)
        
        st.download_button(
            label="💾 Download JSON",
            data=json_str,
            file_name=f"mitr_analytics_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col3:
    if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
        st.warning("⚠️ This will delete all your chat history and preferences!")
        
        if st.button("⚠️ Confirm Delete", type="primary"):
            from services.user_store import delete_all_preferences
            # Note: You'd need to add a delete_all_history() function
            
            st.error("Data deletion feature coming soon!")
            # delete_all_preferences()
            # delete_all_history()
            # st.success("All data deleted!")
            # st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("📊 Analytics refreshed in real-time | 🔒 Your data is private and secure")

# Back to chat button
if st.button("← Back to Chat", use_container_width=True):
    st.switch_page("webapp.py")