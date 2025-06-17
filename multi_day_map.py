import os
import pandas as pd
import folium
from collections import defaultdict


def generate_map(locations, index):
    """
    Generate a map with the trip locations and save it as an HTML file.
    :param locations: List of dictionaries with trip locations containing 'lat', 'lon', 'name', and 'day'.
    :param index: Index for the output file name.
    """
    # Group locations by coordinates to handle multiple days at same place
    location_groups = defaultdict(list)
    locations[-1]['lon'] += 0.0001 # Add epsilon to avoid ignoring connection of first and last identical locations 
    for loc in locations:
        coord_key = (round(loc['lat'], 6), round(loc['lon'], 6),round(loc['Stay_lat'], 6), round(loc['Stay_lon'], 6))  # Round to avoid floating point issues
        location_groups[coord_key].append(loc)
    
    # --- Create map ---
    avg_lat = pd.DataFrame(locations)["lat"].mean()
    avg_lon = pd.DataFrame(locations)["lon"].mean()

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8, tiles='CartoDB positron')
    
    # Create markers for unique locations
    for coord_key, group in location_groups.items():
        lat, lon , lat_stay, lon_stay = coord_key
        
        # Sort days and get all info
        group = sorted(group, key=lambda x: x['day'])
        days = [str(loc['day']) for loc in group]
        location_name = group[0]['name']  # Assuming same location has same name
        
        # Create day display text
        day_display = ','.join(days) if len(days) <= 3 else f"{days[0]}-{days[-1]}"
        
        # Create tooltip with all days
        descriptions = [loc.get('description', '') for loc in group if loc.get('description')]
        tooltip_text = f"Days {','.join(days)}: {location_name}"
        if descriptions:
            tooltip_text += f" - {'; '.join(set(descriptions))}"  # Remove duplicates
        
        # Create popup with detailed info
        popup_content = f"<b>Days {','.join(days)}</b>: {location_name}"
        if descriptions:
            popup_content += f"<br>{'<br>'.join(set(descriptions))}"
        
        div_icon = folium.DivIcon(
            html=f"""
                <div style="
                    font-size: 12pt;
                    color: white;
                    background: rgba(0, 116, 217, 0.35);
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    text-align: center;
                    line-height: 40px;
                    border: 2px solid #001F3F;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                ">{day_display}</div>
            """
        )
    
        # Add larger semi-transparent background node for location grouping
        background_icon = folium.DivIcon(
            html=f"""
                <div style="
                    font-size: 11pt;
                    color: white;
                    background: rgba(220, 20, 60, 0.15);
                    border-radius: 50%;
                    width: 60px;
                    height: 60px;
                    text-align: center;
                    line-height: 60px;
                    border: 2px solid rgba(220, 20, 60, 0.6);
                    box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
                ">({','.join(days)})</div>
            """
        )
        
        # Add background marker first
        folium.Marker(
            location=[lat_stay, lon_stay],
            icon=background_icon
        ).add_to(m)
        
        # Add main marker on top
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=tooltip_text,
            icon=div_icon
        ).add_to(m)

    # Create route using unique locations in day order
    sorted_locations = sorted(locations, key=lambda x: x['day'])
    unique_route = []
    seen_coords = set()
    
    for loc in sorted_locations:
        coord = (round(loc['lat'], 6), round(loc['lon'], 6))
        if coord not in seen_coords:
            unique_route.append((loc["lat"], loc["lon"]))
            seen_coords.add(coord)
    
    # Add route polyline only between unique locations
    if len(unique_route) > 1:
        folium.PolyLine(
            unique_route, 
            color="red", 
            weight=3, 
            opacity=0.8
        ).add_to(m)

    # Save map
    os.makedirs("output", exist_ok=True)
    m.save(f"output/trip_map_{index}.html")
    print("✅ Map saved to output/trip_map.html")