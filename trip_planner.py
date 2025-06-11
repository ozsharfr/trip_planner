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
    
def format_rag_prompt( query: str, llm ) -> str:

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
    result_coords = format_rag_prompt(query=loc['name'], llm=llm_model)
    loc['lat'], loc['lon'] =  result_coords
    print ("Found coordinates for from query: ", result_coords)
    

# --- Load API key ---
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
country = "Romania"
city_start = 'Cluj Napoca'
city_end = city_start
duration = 10
month = "July"


# --- Run LangChain chain ---
#llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
if __name__ == "__main__":

    # --- Prompt for the trip plan ---
    PROMPT = f"""
You are a travel planner and geolocation assistant.

Your task: Plan a {duration}-day family road trip in {country}.

Start point: {city_start}  
End point: {city_end}  
Month: {month}  
Who: Family with young children  
How: Travel by car, staying in apartments.

Preferences:
- Enjoy nature, culture, and relaxation
- Avoid crowded places and long hikes
- Prefer famous, well-known, or natural sites
- Some days can stay in one location; others can include multiple stops

Return the trip as a Python list of dictionaries.
Each dictionary must include:
- 'day': Day number (1 to {duration}) - same day can have multiple locations
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
    
    PROMPT = f"""
You are a travel planner and geolocation assistant.

Step 1: Plan a {duration}-day family road trip in {country}, starting from {city_start} and ending in {city_end}, during {month}.
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
    
    PROMPT_CORRECT = """Here is a list of travel destinations with coordinates.
{result}
Check for:
- Whether each name is a real and locatable place (Nominatim).
- Whether the lat/lon pair matches the place's known location (within ~1 km).
- If any location is invalid, ambiguous, or hallucinated, correct it - with correct lat/lot.

Then return the improved list in the same format."""
    # --- Initialize LLM ---

    llm_model = OllamaLLM(model=MODEL_NAME, base_url=OLLAMA_HOST)

    # Prompt 1
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template=PROMPT
    )   
    
    llm_chain = prompt_template | llm_model

    input_data = {"query": PROMPT}
    t = time.time()
    result = llm_chain.invoke(input_data)
    print (f"Time taken: {time.time() - t:.2f} seconds")

    # Prompt 2
    # Extract the list of locations from the result
    # print("Rechecking result...")
    # prompt_template = PromptTemplate(
    #     input_variables=["query","result"],
    #     template=PROMPT_CORRECT
    # )   
    
    # llm_chain2 = prompt_template | llm_model

    # input_data2 = {"query": PROMPT_CORRECT , "result": result}
    # t = time.time()
    # result = llm_chain2.invoke(input_data2)
    # print (f"Time taken: {time.time() - t:.2f} seconds")


    try:
        locations = eval(result)
    except Exception as e:
        print (f" Error parsing result: {e} , trying to extract list from string.")
        rr = result[result.find('[') : result.find(']')+1]
        locations = eval(rr)

    locations_orig = locations.copy()
    # --- Fill missing coordinates ---
    geolocator = Nominatim(user_agent="trip_planner", timeout=100)
    for loc in locations:
        #if not loc.get("lat") or not loc.get("lon"):
        geo = geolocator.geocode(f"{loc['name']}, {country}")
        # If coordinates are not similar
        #print (loc['name'],'---',geo.longitude, geo.latitude,'---', loc.get("lat"), loc.get("lon"))
        if geo is not None and (abs(geo.latitude - loc.get("lat", 0)) > 0.25 or abs(geo.longitude - loc.get("lon", 0)) > 0.25):
            query_coordinates_from_name(loc, llm_model)
    
    # Detect outliers based on distance
    #locations = locations_orig
    df_locations = pd.DataFrame(locations)
    cols = ["lat", "lon"]
    df_coords = df_locations[cols]
    bool_outlier = (df_coords - df_coords.median()  ).abs() < df_coords.std()*2.5
    df_fix = df_locations.loc[bool_outlier.sum(1)<2]
    for i, row in df_fix.iterrows():
        locations[i] = locations_orig[i]
    # Remove locations with None coordinates
    locations = [loc for loc in locations if loc.get("lat") is not None and loc.get("lon") is not None]

    # --- Create map ---
    avg_lat = pd.DataFrame(locations)["lat"].mean()
    avg_lon = pd.DataFrame(locations)["lon"].mean()

    m = folium.Map(location=[avg_lat , avg_lon],zoom_start=8, tiles='CartoDB positron')
    marker_cluster = MarkerCluster().add_to(m)

    popup_html = f"""
    <div style="font-size: 16px;">
    <b>Day {loc['day']}</b>: {loc['name']}
    </div>
    """
    folium.Marker(
        location=[loc["lat"], loc["lon"]],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Day {loc['day']}: {loc['name']} - {loc.get('description', '')}",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(marker_cluster)

    # Add route polyline
    route = [(loc["lat"], loc["lon"]) for loc in locations]
    folium.PolyLine(route, color="red", weight=3).add_to(m)

    # Save map
    os.makedirs("output", exist_ok=True)
    m.save("output/trip_map.html")
    print("✅ Map saved to output/trip_map.html")
