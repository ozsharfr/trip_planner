import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster


def generate_map(locations, index):
    """
    Generate a map with the trip locations and save it as an HTML file.
    :param locations: List of dictionaries with trip locations containing 'lat', 'lon', 'name', and 'day'.
    :param
    index: Index for the output file name.
    """
    # --- Create map ---
    avg_lat = pd.DataFrame(locations)["lat"].mean()
    avg_lon = pd.DataFrame(locations)["lon"].mean()

    m = folium.Map(location=[avg_lat , avg_lon],zoom_start=8, tiles='CartoDB positron')
    marker_cluster = MarkerCluster().add_to(m)

    for loc in locations:
        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=folium.Popup(f"<b>Day {loc['day']}</b>: {loc['name']}", max_width=250),
            tooltip=f"Day {loc['day']}: {loc['name']} - {loc.get('description', '')}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)

    # Add route polyline
    route = [(loc["lat"], loc["lon"]) for loc in locations]
    folium.PolyLine(route, color="red", weight=3).add_to(m)

    # Save map
    os.makedirs("output", exist_ok=True)
    m.save(f"output/trip_map_{index}.html")
    print("✅ Map saved to output/trip_map.html")