import os
import pandas as pd
import re
import folium
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster
#from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
#from langchain.chains import LLMChain
from langchain_ollama import OllamaLLM
from geopy.distance import geodesic
import time
from dotenv import load_dotenv
from langchain import PromptTemplate

def get_config():
    """
    Load configuration from environment variables.
    """
    load_dotenv()
    class Config:
        MODEL_NAME = os.getenv("MODEL_NAME", "llama3")
        OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY",'')
        country = os.getenv("COUNTRY", "Romania")
        city_start = os.getenv("CITY_START", "Cluj Napoca")
        city_end = os.getenv("CITY_END", "Cluj Napoca")
        duration = int(os.getenv("DURATION", 10))
        month = os.getenv("MONTH", "July")
        composition = os.getenv("COMPOSITION", "a family with young children")

    return Config

def _get_trip_prompt_template(Config):
    """
    Returns the prompt template for generating a trip plan.
    """
    
    PROMPT_BASIC = f"""
You are a travel planner and geolocation assistant.

Step 1: Plan a {Config.duration}-day family road trip in {Config.country}, 
starting from {Config.city_start} and ending in {Config.city_end}, during {Config.month}.
The family has young children, prefers nature and cultural sights, avoids crowds and long hikes, and stays in apartments. The trip should include well-known, geolocatable places.

Step 2: Internally review the trip plan you generated.
Check that:
- Each location name is real and specific enough to be found on Nominatim.
- The coordinates (lat/lon) are accurate within 1 km of the real location.
- There are no invented, ambiguous, or overly generic names.

Step 3: If any location is unclear or inaccurate, revise it using a real-world equivalent.
Return only the improved trip as a Python list of dictionaries, one per day:
- 'day': integer
- 'name': official location name
- 'lat': latitude
- 'lon': longitude
- 'description': short description (optional)

Only return the list. No explanations or notes.
"""
    
    # --- Prompt for the trip plan ---
    PROMPT = f"""
You are a travel planner and geolocation assistant.

Your task: Plan a {Config.duration}-day family road trip in {Config.country}.

Start point: {Config.city_start}  
End point: {Config.city_end}  
Month: {Config.month}  
Who: {Config.composition}  
How: Travel by car, staying in apartments.

Preferences:
- Enjoy nature, culture, and relaxation
- Avoid crowded places and long hikes
- Prefer famous, well-known, or natural sites
- Some days can stay in one location; others can include multiple stops

Return the trip as a Python list of dictionaries.
Each dictionary must include:
- 'day': Day number (1 to {Config.duration}) - same day can have multiple locations
- 'name': Exact name of the location or attraction
- 'lat': Latitude in decimal degrees
- 'lon': Longitude in decimal degrees
- 'description': Short, optional description

VERY IMPORTANT:
- All coordinates ('lat', 'lon') must be real and accurate to within 1 km of the actual location.
- If uncertain, choose well-known landmarks, cities, or attractions that can be accurately located.
- Do NOT invent places. Avoid ambiguous or generic names.
- No more than 3 hours drive per day
- Select locations that Nominatim can recognize.

Only return the list — no extra text or explanation.
"""
    
    
    return PROMPT

def main_plan_prompt(PROMPT: str , llm_model) -> str:
        """
        Main function to generate the trip plan using the LLM.
        """

        prompt_template = PromptTemplate(
        input_variables=["query"],
        template=PROMPT
        )   
        
        llm_chain = prompt_template | llm_model

        input_data = {"query": PROMPT}
        t = time.time()
        result = llm_chain.invoke(input_data)
        print (f"Time taken: {time.time() - t:.2f} seconds")


        return result

def get_coordinates_from_query(result):
    pattern = r"lat\s*:\s*([-\d.]+),\s*lon\s*:\s*([-\d.]+)"
    print (result)
    match = re.search(pattern, result.lower())
    if match:
        lon = float(match.group(1))
        lat = float(match.group(2))
        #print ("xxxx" , lon)
        return (lon , lat)
    else:
        return (None, None)
    
def extract_coords_from_llm_result(result):
        try:
            locations = eval(result)
        except Exception as e:
            print (f" Error parsing result: {e} , trying to extract list from string.")
            rr = result[result.find('[') : result.find(']')+1]
            locations = eval(rr)
        return locations
    
def detect_coords_with_llm( query: str, llm ) -> str:

    # Define the prompt template
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template=
        """You are a highly reliable georgarph.\n
        Can you tell the latitude and longitude coordinates of {query}?
        Answer must be in this pattern, where both 'lat' and 'lon' are mentioned:  (lat : float, lon :float), or None if no reliable answer found
        """
    )
    
    llm_chain = prompt_template | llm | (lambda result : get_coordinates_from_query(result))

    input_data = {"query": query}
    result = llm_chain.invoke(input_data)

    return result

def query_coordinates_from_name(loc: dict  ,llm_model) -> tuple:
    """
    Query coordinates from a location name using geopy.
    If not found, use RAG to get coordinates.
    """
    print(f"Can't find coords for {loc['name']}, looking from query")
    result_coords = detect_coords_with_llm(query=loc['name'], llm=llm_model)
    loc['lat'], loc['lon'] =  result_coords
    print ("Found coordinates for from query: ", result_coords)
    
def validate_location(locations , llm_model ):
        locations_orig = locations.copy()
        # --- Fill missing coordinates ---
        geolocator = Nominatim(user_agent="trip_planner", timeout=100)
        for loc in locations:
            #if not loc.get("lat") or not loc.get("lon"):
            geo = geolocator.geocode(f"{loc['name']}")
            # If coordinates are not similar
            #print (loc['name'],'---',geo.longitude, geo.latitude,'---', loc.get("lat"), loc.get("lon"))
            if geo is not None and (abs(geo.latitude - loc.get("lat", 0)) > 0.25 or abs(geo.longitude - loc.get("lon", 0)) > 0.25):
                query_coordinates_from_name(loc, llm_model)
        
        return locations , locations_orig

def ignore_null_coords_locations(locations , locations_orig, index , ignore_geolocator=False):
        df_locations = pd.DataFrame(locations)
        cols = ["lat", "lon"]
        df_coords = df_locations[cols]
        df_locations.to_csv(f"output/locations{index}.csv", index=False)
        bool_outlier = (df_coords - df_coords.median()  ).abs() < df_coords.std()*2.5
        df_fix = df_locations.loc[bool_outlier.sum(1)<2]
        if ignore_geolocator:
            for i, row in df_fix.iterrows():
                locations[i] = locations_orig[i]
        # Remove locations with None coordinates
        locations = [loc for loc in locations if loc.get("lat") is not None and loc.get("lon") is not None]
        return locations

def generate_map(locations, index):

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

# --- Run LangChain chain ---
#llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
def main(index=0):

    Config = get_config()

    PROMPT = _get_trip_prompt_template(Config)
    # --- Initialize LLM ---

    llm_model = OllamaLLM(model=Config.MODEL_NAME, base_url=Config.OLLAMA_HOST)
    
    result = main_plan_prompt(PROMPT, llm_model)
    locations = extract_coords_from_llm_result(result)

    locations , locations_orig = validate_location(locations , llm_model)
    # Detect outliers based on distance

    locations = ignore_null_coords_locations(locations , locations_orig, index , ignore_geolocator=False)
    generate_map(locations, index)
    
if __name__ == "__main__":
    for index in range(5):
        print(f"Running trip planner iteration {index + 1}...")
        main(index)
