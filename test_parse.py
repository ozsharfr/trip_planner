from extract_coordinates import extract_coords_from_llm_result
from remove_problemtaic_coords import ignore_null_coords_locations
from multi_day_map import generate_map

index = 11
result = "Here is the planned trip:\n\n[\n{'day': 1, 'name': 'Sofia', 'lat': 42.6974, 'lon': 23.3235, 'Stay_lat': 42.6963, 'Stay_lon': 23.3226, 'description': 'Arrival in Sofia'},\n{'day': 2, 'name': 'Boyana Waterfall', 'lat': 42.6237, 'lon': 23.2459, 'Stay_lat': 42.6963, 'Stay_lon': 23.3226, 'description': 'Relaxation'},\n{'day': 2, 'name': 'Sofia', 'lat': 42.6974, 'lon': 23.3235, 'Stay_lat': 42.6963, 'Stay_lon': 23.3226, 'description': ''},\n{'day': 3, 'name': 'Plovdiv', 'lat': 42.1489, 'lon': 24.7458, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Explore Plovdiv'},\n{'day': 4, 'name': 'Asenovgrad', 'lat': 42.0456, 'lon': 24.8447, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Visit Bachkovo Monastery'},\n{'day': 5, 'name': 'Koprivshtitsa', 'lat': 42.3649, 'lon': 24.3333, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Explore Koprivshtitsa'},\n{'day': 6, 'name': 'Bansko', 'lat': 41.7785, 'lon': 23.5094, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Relaxation'},\n{'day': 7, 'name': 'Smolyan', 'lat': 41.4553, 'lon': 24.7448, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Explore Smolyan Lake'},\n{'day': 8, 'name': 'Pamporovo', 'lat': 41.5833, 'lon': 25.0833, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Relaxation'},\n{'day': 9, 'name': 'Sinite Kamani Waterfall', 'lat': 41.8667, 'lon': 25.2333, 'Stay_lat': 42.1231, 'Stay_lon': 24.7222, 'description': 'Hike and relax'},\n{'day': 10, 'name': 'Varna', 'lat': 43.2167, 'lon': 27. organizes', 'Stay_lat': 43.2179, 'Stay_lon': 27. in, 'description': 'Arrival in Varna'}\n]"

locations = extract_coords_from_llm_result(result)


locations_orig = locations.copy()
    # Detect and remove locations which are way too far from most locations
locations = ignore_null_coords_locations(locations , locations_orig, index ,
                                             threshold_km=150, ignore_geolocator=False)

    # --- Generate map with planned route---
generate_map(locations, index)