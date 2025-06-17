from langchain.prompts import PromptTemplate
import time

def _get_trip_prompt_template(Config):
    """
    Returns the prompt template for generating a trip plan.
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
- No more than 2.5 hours drive per day
- No more than 300 kilometers per day
- Select locations that Nominatim can recognize.


Only return the list — no extra text or explanation.
"""
    
    
    return PROMPT

def _get_trip_prompt_template(Config):
    """
    Returns the prompt template for generating a trip plan.
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
- Prefer well-known, or natural sites
- Aim to build the route which will enable as least hoteling switches as possible 

Return the trip as a Python list of dictionaries.
Each dictionary must include:
- 'day': Day number (1 to {Config.duration}) - same day can have multiple locations
- 'name': Exact name of the location or attraction
- 'lat': Latitude in decimal degrees
- 'lon': Longitude in decimal degrees
- 'Stay_lat' : Latitude in decimal degree of the place where staying at night
- 'Stay_lon' : Longitude in decimal degree of the place where staying at night
- 'description': Short, optional description

VERY IMPORTANT:
- All coordinates ('lat', 'lon') must be real and accurate to within 1 km of the actual location.
- If uncertain, choose well-known landmarks, cities, or attractions that can be accurately located.
- Do NOT invent places. Avoid ambiguous or generic names.Select locations that Nominatim can recognize.
- No more than 2.5 hours drive per day
- No more than {Config.max_km_dist_per_day * 1.5} kilometers per day


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