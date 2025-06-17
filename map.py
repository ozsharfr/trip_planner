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

        day_number = loc['day']
        div_icon = folium.DivIcon(
            html=f"""
                <div style="
                    font-size: 14pt;
                    color: white;
                    background: #0074D9;
                    border-radius: 50%;
                    width: 36px;
                    height: 36px;
                    text-align: center;
                    line-height: 36px;
                    border: 2px solid #001F3F;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                ">{day_number}</div>
            """
        )
    
        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=folium.Popup(f"<b>Day {loc['day']}</b>: {loc['name']}", max_width=250),
            tooltip=f"Day {loc['day']}: {loc['name']} - {loc.get('description', '')}",
            icon=div_icon#folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)

    # Add route polyline
    route = [(loc["lat"], loc["lon"]) for loc in locations]
    folium.PolyLine(route, color="red", weight=3).add_to(m)

    # Save map
    os.makedirs("output", exist_ok=True)
    m.save(f"output/trip_map_{index}.html")
    print("✅ Map saved to output/trip_map.html")