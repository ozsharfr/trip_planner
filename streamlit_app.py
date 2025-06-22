import streamlit as st
from main import main_plan_prompt, extract_coords_from_llm_result, ignore_null_coords_locations, generate_map
from prompt_trip import main_plan_prompt , _get_trip_prompt_template

# Simple config class to mimic the original get_config() structure
class ConfigObj:
    def __init__(self, country, city_start, city_end, composition, max_km, duration, month, preferences):
        self.country = country
        self.city_start = city_start
        self.city_end = city_end
        self.composition = composition
        self.max_km_dist_per_day = max_km
        self.duration = duration
        self.month = month
        self.GROQ_API_KEY='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'
        self.NUM_ITERATIONS=5
        # Add step of locations validations
        self.LOCATION_VAL=False
        self.preferences = preferences

st.title("🗺️ Travel Itinerary Generator")

with st.form("trip_form"):
    country = st.text_input("Country", "Romania")
    city_start = st.text_input("Start City", "Cluj Napoca")
    city_end = st.text_input("End City", "Cluj Napoca")
    composition = st.selectbox("Travel Composition", ["Family with children", "Couple", "Solo", "Group"])
    preferences = st.multiselect(
    "What kind of experiences do you prefer?",
    [
        "Nature", "Culture", "Relaxation", "Adventure",
        "Food & Culinary", "Family-friendly", "Romantic",
        "City Life", "History", "Wildlife & Safari",
        "Spiritual/Wellness", "Budget Travel", "Luxury Travel", "Photography"
    ],
    default=["Nature", "Culture", "Relaxation"]  # Optional default
)
    max_km = st.slider("Max distance per day (km)", 50, 500, 200)
    duration = st.slider("Trip Duration (days)", 1, 30, 10)
    month = st.selectbox("Month of Travel", ["January" , "February" , "march" , "April" , "May", 
                                             "June", "July", "August", "September",
                                             "October", "November", "December"])
    
    submitted = st.form_submit_button("Generate Itinerary")

if submitted:
    st.info("Generating trip... This may take a few seconds.")
    
    # Create config
    Config = ConfigObj(country, city_start, city_end, composition, max_km, duration, month, preferences)
    
    # Prompt + process
    prompt = _get_trip_prompt_template(Config)
    result = main_plan_prompt(prompt, Config)
    locations = extract_coords_from_llm_result(result)
    locations_orig = locations.copy()
    locations = ignore_null_coords_locations(locations, locations_orig, 0,
                                             threshold_km=Config.max_km_dist_per_day,
                                             ignore_geolocator=False)

    # Save and display the map
    
    generate_map(locations, 0)

    st.success("Trip generated - In blue circles locations to vist, in red circles locations to stay overnight.")
    st.components.v1.html(open(f"./output/trip_map_0.html", "r", encoding="utf-8").read(), height=500 , width=800)
