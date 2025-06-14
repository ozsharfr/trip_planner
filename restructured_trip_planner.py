"""
Trip Planner - Restructured Version
A modular trip planning application using LLM and geolocation services.
"""

import os
import pandas as pd
import re
import folium
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from geopy.distance import geodesic
from dotenv import load_dotenv


@dataclass
class Location:
    """Represents a travel location with coordinates and metadata."""
    day: int
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    description: str = ""
    
    def has_coordinates(self) -> bool:
        """Check if location has valid coordinates."""
        return self.lat is not None and self.lon is not None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for compatibility."""
        return {
            'day': self.day,
            'name': self.name,
            'lat': self.lat,
            'lon': self.lon,
            'description': self.description
        }


@dataclass
class TripConfig:
    """Configuration for trip planning."""
    country: str = "Romania"
    city_start: str = "Cluj Napoca"
    city_end: str = "Cluj Napoca"
    duration: int = 10
    month: str = "July"
    model_name: str = "llama3"
    ollama_host: str = "http://localhost:11434"


class CoordinateExtractor:
    """Handles coordinate extraction from LLM responses."""
    
    @staticmethod
    def extract_from_text(text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract lat/lon coordinates from text using regex."""
        pattern = r"lat\s*:\s*([-\d.]+),\s*lon\s*:\s*([-\d.]+)"
        match = re.search(pattern, text.lower())
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return (lat, lon)
        return (None, None)
    
    @staticmethod
    def extract_locations_list(result: str) -> List[Dict]:
        """Extract list of locations from LLM result."""
        try:
            locations = eval(result)
        except Exception as e:
            print(f"Error parsing result: {e}, trying to extract list from string.")
            start = result.find('[')
            end = result.find(']') + 1
            if start != -1 and end != 0:
                locations = eval(result[start:end])
            else:
                raise ValueError("Could not extract locations list from result")
        return locations


class LLMService:
    """Handles LLM interactions for trip planning and coordinate detection."""
    
    def __init__(self, model_name: str, base_url: str):
        self.llm = OllamaLLM(model=model_name, base_url=base_url)
    
    def generate_trip_plan(self, config: TripConfig) -> str:
        """Generate trip plan using LLM."""
        prompt_template = PromptTemplate(
            input_variables=["country", "duration", "city_start", "city_end", "month"],
            template=self._get_trip_prompt_template()
        )
        
        chain = prompt_template | self.llm
        
        input_data = {
            "country": config.country,
            "duration": config.duration,
            "city_start": config.city_start,
            "city_end": config.city_end,
            "month": config.month
        }
        
        start_time = time.time()
        result = chain.invoke(input_data)
        print(f"LLM response time: {time.time() - start_time:.2f} seconds")
        
        return result
    
    def detect_coordinates(self, location_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Detect coordinates for a location using LLM."""
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""You are a highly reliable geographer.
            Can you tell the latitude and longitude coordinates of {query}?
            Answer must be in this pattern, where both 'lat' and 'lon' are mentioned: 
            (lat : float, lon : float), or None if no reliable answer found"""
        )
        
        chain = prompt_template | self.llm
        result = chain.invoke({"query": location_name})
        
        return CoordinateExtractor.extract_from_text(result)
    
    def _get_trip_prompt_template(self) -> str:
        """Get the trip planning prompt template."""
        return """
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


class GeolocationValidator:
    """Validates and corrects location coordinates."""
    
    def __init__(self, llm_service: LLMService):
        self.geolocator = Nominatim(user_agent="trip_planner", timeout=100)
        self.llm_service = llm_service
    
    def validate_locations(self, locations: List[Location], country: str) -> List[Location]:
        """Validate and correct location coordinates."""
        for location in locations:
            if not location.has_coordinates():
                continue
                
            # Try to geocode the location
            geo_result = self.geolocator.geocode(f"{location.name}, {country}")
            
            if geo_result is None:
                print(f"Warning: Could not geocode {location.name}")
                continue
            
            # Check if coordinates are significantly different
            lat_diff = abs(geo_result.latitude - location.lat)
            lon_diff = abs(geo_result.longitude - location.lon)
            
            if lat_diff > 0.25 or lon_diff > 0.25:
                print(f"Large coordinate difference for {location.name}, using LLM detection")
                new_lat, new_lon = self.llm_service.detect_coordinates(location.name)
                if new_lat is not None and new_lon is not None:
                    location.lat = new_lat
                    location.lon = new_lon
        
        return locations
    
    def filter_outliers(self, locations: List[Location]) -> List[Location]:
        """Remove locations with outlier coordinates or missing data."""
        # Filter out locations without coordinates
        valid_locations = [loc for loc in locations if loc.has_coordinates()]
        
        if len(valid_locations) < 3:
            return valid_locations
        
        # Convert to DataFrame for outlier detection
        df = pd.DataFrame([{'lat': loc.lat, 'lon': loc.lon} for loc in valid_locations])
        
        # Simple outlier detection using standard deviation
        bool_outlier = (df - df.median()).abs() < df.std() * 2.5
        outlier_mask = bool_outlier.sum(axis=1) >= 2
        
        return [loc for i, loc in enumerate(valid_locations) if outlier_mask.iloc[i]]


class MapGenerator:
    """Generates interactive maps for trip visualization."""
    
    @staticmethod
    def generate_trip_map(locations: List[Location], output_path: str) -> None:
        """Generate an interactive map with trip locations."""
        if not locations:
            print("No valid locations to map")
            return
        
        # Calculate center point
        lats = [loc.lat for loc in locations if loc.has_coordinates()]
        lons = [loc.lon for loc in locations if loc.has_coordinates()]
        
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create map
        trip_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='CartoDB positron'
        )
        
        marker_cluster = MarkerCluster().add_to(trip_map)
        
        # Add markers
        for location in locations:
            if not location.has_coordinates():
                continue
                
            folium.Marker(
                location=[location.lat, location.lon],
                popup=folium.Popup(
                    f"<b>Day {location.day}</b>: {location.name}", 
                    max_width=250
                ),
                tooltip=f"Day {location.day}: {location.name} - {location.description}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(marker_cluster)
        
        # Add route polyline
        route_coords = [(loc.lat, loc.lon) for loc in locations if loc.has_coordinates()]
        if len(route_coords) > 1:
            folium.PolyLine(route_coords, color="red", weight=3).add_to(trip_map)
        
        # Save map
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        trip_map.save(output_path)
        print(f"✅ Map saved to {output_path}")


class TripPlanner:
    """Main trip planner orchestrator."""
    
    def __init__(self, config: TripConfig):
        self.config = config
        self.llm_service = LLMService(config.model_name, config.ollama_host)
        self.validator = GeolocationValidator(self.llm_service)
        self.map_generator = MapGenerator()
    
    def plan_trip(self, iteration: int = 0) -> List[Location]:
        """Plan a complete trip and generate map."""
        print(f"Planning trip iteration {iteration + 1}...")
        
        # Generate trip plan using LLM
        llm_result = self.llm_service.generate_trip_plan(self.config)
        
        # Extract locations from LLM result
        locations_data = CoordinateExtractor.extract_locations_list(llm_result)
        locations = [Location(**loc_data) for loc_data in locations_data]
        
        # Validate and correct coordinates
        locations = self.validator.validate_locations(locations, self.config.country)
        
        # Filter outliers and invalid locations
        locations = self.validator.filter_outliers(locations)
        
        # Generate map
        output_path = f"output/trip_map_{iteration}.html"
        self.map_generator.generate_trip_map(locations, output_path)
        
        # Save coordinates to CSV
        self._save_coordinates_csv(locations, iteration)
        
        return locations
    
    def _save_coordinates_csv(self, locations: List[Location], iteration: int) -> None:
        """Save location coordinates to CSV file."""
        if not locations:
            return
            
        df = pd.DataFrame([
            {'lat': loc.lat, 'lon': loc.lon} 
            for loc in locations if loc.has_coordinates()
        ])
        
        os.makedirs("output", exist_ok=True)
        df.to_csv(f"output/coords_{iteration}.csv", index=False)


def main():
    """Main entry point."""
    load_dotenv()
    
    # Create configuration
    config = TripConfig(
        country=os.getenv("COUNTRY", "Romania"),
        city_start=os.getenv("CITY_START", "Cluj Napoca"),
        city_end=os.getenv("CITY_END", "Cluj Napoca"),
        duration=int(os.getenv("DURATION", "10")),
        month=os.getenv("MONTH", "July"),
        model_name=os.getenv("MODEL_NAME", "llama3"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    
    # Create trip planner
    planner = TripPlanner(config)
    
    # Generate multiple trip variations
    num_iterations = int(os.getenv("NUM_ITERATIONS", "5"))
    for i in range(num_iterations):
        try:
            locations = planner.plan_trip(i)
            print(f"Trip {i + 1} completed with {len(locations)} locations")
        except Exception as e:
            print(f"Error in trip {i + 1}: {e}")


if __name__ == "__main__":
    main()
