
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from extract_coordinates import extract_coords_from_llm_result
from multi_day_map import generate_map
from config import get_config
from remove_problemtaic_coords import ignore_null_coords_locations
from prompt_trip import main_plan_prompt , _get_trip_prompt_template
from agent_trip import try_agent
from validate_locations_coords import validate_location

# --- Run LangChain chain ---

def main(index=0):
    """
    Main function to run the trip planner.
    Args:
        index (int): Index for the trip iteration, used for generating unique filenames.
    """
    # --- Load configuration ---

    Config = get_config()

    PROMPT = _get_trip_prompt_template(Config)
    # --- Initialize LLM ---
    # 
    # Use the current working model
    # Run the main prompt to get the trip plan
    result = main_plan_prompt(PROMPT , Config)
    # --- Extract locations coordinates from the LLM result ---
    locations = extract_coords_from_llm_result(result)

    # Validate with geolocator. If coordinates significantly differ - query them again using LLM
    # if Config.location_val:    
    #     locations , locations_orig = validate_location(locations , llm_model)
    # else:
    #     locations_orig = locations.copy()
    locations_orig = locations.copy()
    # Detect and remove locations which are way too far from most locations
    locations = ignore_null_coords_locations(locations , locations_orig, index ,
                                             threshold_km=Config.max_km_dist_per_day, ignore_geolocator=False)

    # --- Generate map with planned route---
    generate_map(locations, index)
    
if __name__ == "__main__":
    Config = get_config()
    for index in range(1):
        print(f"Running trip planner iteration {index + 1}...")
        main(index)
