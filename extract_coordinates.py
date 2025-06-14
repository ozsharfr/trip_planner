import re
import ast
from langchain.prompts import PromptTemplate

def get_coordinates_from_query(result):
    pattern = r"lat\s*:\s*([-\d.]+),\s*lon\s*:\s*([-\d.]+)"
    print (result)
    match = re.search(pattern, result.lower())
    if match:
        lon = float(match.group(1))
        lat = float(match.group(2))
        return (lon , lat)
    else:
        return (None, None)

def safe_extract_locations(llm_output: str):
    """
    Extracts a list of trip locations from the LLM output string.
    Handles extra text and mild formatting errors.
    """
    # 1. Try to extract the list part only
    start = llm_output.find('[')
    end = llm_output.rfind(']') + 1
    if start == -1 or end == -1:
        print("Could not find list brackets in output.")
        return []

    list_str = llm_output[start:end]

    # 2. Sanitize broken float values (e.g., '27. organizes')
    list_str = re.sub(r":\s*[\d]+\.\s*[a-zA-Z]+", ': null', list_str)

    # 3. Try to parse using ast.literal_eval
    try:
        locations = ast.literal_eval(list_str)
    except Exception as e:
        print(f"Failed to parse locations: {e}")
        return []

    # 4. Validate lat/lon fields
    for loc in locations:
        for key in ['lat', 'lon']:
            try:
                loc[key] = float(loc[key])
            except:
                loc[key] = None  # fallback mechanism will fix later

    return locations

   
def extract_coords_from_llm_result(result):
        try:
            locations = eval(result)
        except Exception as e:
            print (f" Error parsing result: {e} , trying to extract list from string.")
            locations = safe_extract_locations(result)
        return locations
    
