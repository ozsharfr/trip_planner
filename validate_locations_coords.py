from geopy.geocoders import Nominatim
from langchain.prompts import PromptTemplate
import re
from extract_coordinates import get_coordinates_from_query

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
            if geo is not None and (abs(geo.latitude - loc.get("lat", 0)) > 0.25 or abs(geo.longitude - loc.get("lon", 0)) > 0.25):
                query_coordinates_from_name(loc, llm_model)
        
        return locations , locations_orig