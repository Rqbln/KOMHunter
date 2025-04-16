import streamlit as st
import folium
from streamlit_folium import folium_static
from strava_client import get_my_last_activities
from segment_scoring import compute_difficulty
from strava_auth import authenticate
from stravalib import unit_helper
from folium import plugins
from strava_api import explore_segments, get_segment_details
import time
import requests

st.set_page_config(page_title="Strava KOM Hunter", layout="wide")

st.title("🏆 Strava KOM Hunter")
st.markdown("Find and visualize your easiest segments to conquer!")

st.sidebar.header("Settings")
sport_type = st.sidebar.selectbox("Sport type", ["Run", "Ride"])
max_segments = st.sidebar.slider("Number of segments to display", 1, 10, 10)

# Search area settings
st.sidebar.header("Segment Search")
radius_km = st.sidebar.slider("Search radius (km)", 1, 50, 10)
location_search = st.sidebar.text_input("Search location (city, address...)", value="Paris, France")

# Function to geocode location
def geocode_location(location_query):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1"
        headers = {"User-Agent": "KOMHunter/1.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon, data[0].get("display_name", location_query)
        else:
            return 48.7016, 2.1341, "Paris, France (default)"  # Default to Paris if not found
    except Exception as e:
        st.warning(f"Geocoding error: {e}. Using default location.")
        return 48.7016, 2.1341, "Paris, France (default)"

# Auth + fetch user info
try:
    client = authenticate()
    athlete = client.get_athlete()
    st.sidebar.success(f"👋 Hello, {athlete.firstname} {athlete.lastname}")
except Exception as e:
    st.error(f"❌ Strava authentication failed: `{e}`")
    st.stop()

# Convert location search to coordinates
search_lat, search_lon, location_name = geocode_location(location_search)

# Create a clean, simple layout
st.subheader(f"🗺️ Segments Explorer")

# Button to trigger segment exploration
explore_button = st.button("🔍 Explorer les segments", type="primary")

# Only create these containers once
map_container = st.empty()
progress_bar = st.empty()
status_text = st.empty()
results_container = st.empty()

# Initialize the map with the search location - this ensures the geocoding happens once
if not explore_button:
    with map_container:
        main_map = folium.Map(location=[search_lat, search_lon], zoom_start=12)
        folium.Circle(
            location=[search_lat, search_lon],
            radius=radius_km * 1000,  # km to meters
            color='blue',
            fill=True,
            fill_opacity=0.2
        ).add_to(main_map)
        folium.plugins.Fullscreen().add_to(main_map)
        folium.plugins.LocateControl().add_to(main_map)
        folium_static(main_map)

if explore_button:
    # Clear previous results
    map_container.empty()
    
    # Create a new map with updated location
    main_map = folium.Map(location=[search_lat, search_lon], zoom_start=12)
    folium.Circle(
        location=[search_lat, search_lon],
        radius=radius_km * 1000,
        color='blue',
        fill=True,
        fill_opacity=0.2
    ).add_to(main_map)
    folium.plugins.Fullscreen().add_to(main_map)
    folium.plugins.LocateControl().add_to(main_map)
    folium.LayerControl().add_to(main_map)
    
    try:
        # Setup a progress bar
        p_bar = progress_bar.progress(0, text="Recherche des segments en cours...")
        
        # Get segments in the area
        area_segments = explore_segments(
            client.access_token, 
            search_lat, 
            search_lon, 
            radius_km=radius_km, 
            activity_type=sport_type,
            max_segments=max_segments
        )
        
        # Update progress
        p_bar.progress(10, text="Segments trouvés, analyse en cours...")
        
        if area_segments and len(area_segments) > 0:
            # Prepare data for table
            segment_data = []
            
            # Process each segment
            for i, seg in enumerate(area_segments):
                segment_id = seg["id"]
                status_text.text(f"Analyse du segment: {seg['name']} ({i+1}/{len(area_segments)})")
                
                try:
                    # Get detailed segment information including KOM
                    segment_details = get_segment_details(client.access_token, segment_id)
                    
                    # Add data for table
                    kom_name = "N/A"
                    kom_time = "N/A"
                    
                    if segment_details.get("kom_data"):
                        kom_name = segment_details["kom_data"]["athlete_name"]
                        kom_time = segment_details["kom_data"]["elapsed_time_formatted"]
                    
                    segment_data.append({
                        "ID": seg["id"],
                        "Segment": seg["name"],
                        "Distance": f"{seg['distance']/1000:.2f} km",
                        "Grade": f"{seg['avg_grade']:.1f}%",
                        "KOM": kom_name,
                        "Time": kom_time
                    })
                    
                    # Create popup content
                    popup_html = f"""
                    <div style="min-width: 200px;">
                        <h4>{seg['name']}</h4>
                        <b>Distance:</b> {seg['distance']/1000:.2f} km<br>
                        <b>Grade:</b> {seg['avg_grade']:.1f}%<br>
                        <b>KOM:</b> {kom_name}<br>
                        <b>Time:</b> {kom_time}<br>
                        <a href="https://www.strava.com/segments/{segment_id}" target="_blank">View on Strava</a>
                    </div>
                    """
                    
                    # Get segment points
                    if "detailed_points" in segment_details and len(segment_details["detailed_points"]) > 2:
                        segment_points = segment_details["detailed_points"]
                    else:
                        # Fallback to start and end
                        start_lat, start_lon = seg["start_latlng"]
                        end_lat, end_lon = seg["end_latlng"]
                        segment_points = [[start_lat, start_lon], [end_lat, end_lon]]
                    
                    # Add segment to map
                    folium.PolyLine(
                        locations=segment_points,
                        color='red',
                        weight=3,
                        opacity=0.7,
                        popup=folium.Popup(popup_html, max_width=300)
                    ).add_to(main_map)
                    
                    # Add marker at start
                    start_lat, start_lon = seg["start_latlng"]
                    folium.Marker(
                        [start_lat, start_lon],
                        icon=folium.Icon(color='green', icon='play', prefix='fa'),
                        popup=folium.Popup(f"Start: {seg['name']}", max_width=300)
                    ).add_to(main_map)
                    
                    # Update progress
                    progress_value = 10 + int(90 * (i + 1) / len(area_segments))
                    p_bar.progress(progress_value, text=f"Analyse des segments: {i+1}/{len(area_segments)}")
                    
                except Exception as detail_error:
                    # Just skip problematic segments
                    pass
            
            # Show the map and data once fully processed
            map_container.empty()
            with map_container:
                folium_static(main_map)
            
            # Clean up progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display results table
            if len(segment_data) > 0:
                results_container.dataframe(segment_data, use_container_width=True, 
                                           column_config={
                                               "ID": st.column_config.NumberColumn("ID"),
                                               "Segment": st.column_config.TextColumn("Segment"),
                                               "Distance": st.column_config.TextColumn("Distance"),
                                               "Grade": st.column_config.TextColumn("Grade (%)"),
                                               "KOM": st.column_config.TextColumn("KOM Holder"),
                                               "Time": st.column_config.TextColumn("KOM Time")
                                           })
            else:
                results_container.warning("Aucun segment trouvé avec des détails complets")
        else:
            # No segments found
            progress_bar.empty()
            status_text.empty()
            results_container.info("Aucun segment trouvé dans cette zone")
            
            # Still show the map
            map_container.empty()
            with map_container:
                folium_static(main_map)
    
    except Exception as e:
        # Error handling
        progress_bar.empty()
        status_text.empty()
        results_container.error(f"Erreur: {e}")
