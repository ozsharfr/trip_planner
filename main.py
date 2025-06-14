
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from extract_coordinates import extract_coords_from_llm_result
from map import generate_map
from config import get_config
from remove_problemtaic_coords import ignore_null_coords_locations
from prompt_trip import main_plan_prompt , _get_trip_prompt_template
from agent_trip import try_agent

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
    llm_model = OllamaLLM(model=Config.MODEL_NAME, base_url=Config.OLLAMA_HOST)
    # Run the main prompt to get the trip plan
    result = main_plan_prompt(PROMPT, llm_model)
    # --- Extract locations coordinates from the LLM result ---
    locations = extract_coords_from_llm_result(result)

    # Experimental : # Uncomment to use an agent to validate and improve the trip plan
    # locations_w_agent = try_agent(locations, llm_model)

    # Validate with geolocator. If coordinates significantly differ - query them again using LLM
    #locations , locations_orig = validate_location(locations , llm_model)
    locations_orig = locations.copy()

    # Detect and remove locations which are way too far from most locations
    locations = ignore_null_coords_locations(locations , locations_orig, index , ignore_geolocator=False)
    # --- Generate map with planned route---
    generate_map(locations, index)
    
if __name__ == "__main__":
    Config = get_config()
    for index in range(2):
        print(f"Running trip planner iteration {index + 1}...")
        main(index)
