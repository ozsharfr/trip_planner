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

def fix_mix_or_trail(list_str):
        lines = list_str.strip().splitlines()
        clean_lines = []
        for line in lines:
            line_cleaned = line.strip()
            # Heuristic: keep only lines that end with }, or }
            if line_cleaned.endswith("},") or line_cleaned.endswith("}"):
                clean_lines.append(line_cleaned)
            else:
                print(f"Skipping malformed line: {line_cleaned}")

        clean_list_str = "[" + "\n".join(clean_lines) + "]"

        return clean_list_str

def safe_extract_locations(llm_output: str):
    """
    Safely extracts a list of trip locations from LLM output, correcting
    broken floats, JSON-style nulls, and truncated lines.
    """

    # 1. Extract the list
    start = llm_output.find('[')
    end = llm_output.rfind(']') + 1
    if start == -1 or end == -1:
        print("Could not find list brackets.")
        return []

    list_str = llm_output[start:end]

    # 2. Normalize JSON-style to Python
    list_str = list_str.replace("null", "None").replace("true", "True").replace("false", "False")

    # 3. Replace broken float-like values with None (handles: 27. organ')
    list_str = re.sub(r":\s*\d+\.\s+[a-zA-Z]+'?", ": None", list_str)
               
    try:
        locations = ast.literal_eval(list_str)
    except Exception as e:
        print ("Error in parsing, trying to fix for mix of letters in lat/lon")
        # 4. Optionally fix trailing commas inside lists
        clean_list_str = fix_mix_or_trail(list_str)
        # 5. Evaluate
        try:
            locations = ast.literal_eval(clean_list_str)
        except Exception as e:
            print(f"Still failed to parse: {e}")
            return []

    # 6. Force lat/lon to float or None
    for loc in locations:
        for key in ['lat', 'lon']:
            try:
                loc[key] = float(loc[key])
            except:
                loc[key] = None

    return locations


   
def extract_coords_from_llm_result(result):
        try:
            locations = eval(result)
        except Exception as e:
            print (f" Error parsing result: {e} , trying to extract list from string.")
            locations = safe_extract_locations(result)
        return locations
    
