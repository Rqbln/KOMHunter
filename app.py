import streamlit as st
import folium
from streamlit_folium import folium_static
from strava_client import get_my_last_activities
from segment_scoring import compute_difficulty
from stravalib import unit_helper

st.set_page_config(page_title="Strava KOM Hunter", layout="wide")

st.title("🏆 Strava KOM Hunter")
st.markdown("Find and visualize your easiest segments to conquer!")

st.sidebar.header("Settings")
sport_type = st.sidebar.selectbox("Sport type", ["Run", "Ride"])
limit = st.sidebar.slider("Number of recent activities to analyze", 1, 50, 10)

activities = get_my_last_activities(limit=limit)

segments = []
for act in activities:
    if act.type != sport_type:
        continue
    if not hasattr(act, "segment_efforts"):
        continue
    for effort in act.segment_efforts:
        seg = effort.segment
        try:
            score = compute_difficulty(
                seg.distance.magnitude,
                seg.total_elevation_gain.magnitude,
                seg.kom_elevation_high / effort.elapsed_time.total_seconds() * 3.6
            )
        except Exception:
            score = 9999

        segments.append({
            "name": seg.name,
            "lat": seg.start_latlng.lat if seg.start_latlng else 0,
            "lon": seg.start_latlng.lon if seg.start_latlng else 0,
            "distance": unit_helper.kilometers(seg.distance).magnitude,
            "elev": seg.total_elevation_gain,
            "score": score
        })

# Display segments on a folium map
if segments:
    st.subheader("📍 Easy Segments Found")
    m = folium.Map(location=[segments[0]["lat"], segments[0]["lon"]], zoom_start=13)
    for s in sorted(segments, key=lambda x: x["score"])[:10]:
        popup = f"{s['name']}<br>Distance: {s['distance']} km<br>Score: {s['score']}"
        folium.Marker([s["lat"], s["lon"]], popup=popup).add_to(m)

    folium_static(m)
else:
    st.warning("No matching segments found in your recent activities.")
