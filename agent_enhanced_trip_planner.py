"""
Agent-Enhanced Trip Planner
Uses LangChain agents with specialized tools for intelligent trip planning.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain.schema import AgentAction, AgentFinish
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
import pandas as pd
from dotenv import load_dotenv


@dataclass
class TripConfig:
    """Enhanced configuration for agent-based trip planning."""
    country: str = "Romania"
    city_start: str = "Cluj Napoca"
    city_end: str = "Cluj Napoca"
    duration: int = 10
    month: str = "July"
    budget: str = "moderate"  # low, moderate, high
    interests: List[str] = None
    model_name: str = "llama3"
    ollama_host: str = "http://localhost:11434"
    
    def __post_init__(self):
        if self.interests is None:
            self.interests = ["nature", "culture", "family-friendly"]


class GeolocationTool:
    """Tool for accurate geolocation services."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="trip_planner_agent", timeout=10)
    
    def geocode_location(self, location_name: str, country: str = None) -> Dict:
        """Get coordinates and detailed info for a location."""
        query = f"{location_name}, {country}" if country else location_name
        
        try:
            result = self.geolocator.geocode(query, exactly_one=True)
            if result:
                return {
                    "name": result.address,
                    "lat": result.latitude,
                    "lon": result.longitude,
                    "found": True,
                    "confidence": "high"
                }
            else:
                return {"found": False, "error": "Location not found"}
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def validate_coordinates(self, lat: float, lon: float, expected_name: str) -> Dict:
        """Validate if coordinates match expected location."""
        try:
            result = self.geolocator.reverse((lat, lon), exactly_one=True)
            if result:
                return {
                    "valid": True,
                    "actual_name": result.address,
                    "matches_expected": expected_name.lower() in result.address.lower()
                }
            return {"valid": False, "error": "No location found at coordinates"}
        except Exception as e:
            return {"valid": False, "error": str(e)}


class DistanceTool:
    """Tool for calculating distances and travel times."""
    
    @staticmethod
    def calculate_distance(point1: tuple, point2: tuple) -> Dict:
        """Calculate distance between two points."""
        try:
            distance = geodesic(point1, point2).kilometers
            # Rough driving time estimate (60 km/h average)
            drive_time_hours = distance / 60
            
            return {
                "distance_km": round(distance, 2),
                "drive_time_hours": round(drive_time_hours, 2),
                "feasible_day_trip": drive_time_hours <= 3
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def validate_daily_distances(locations: List[Dict]) -> Dict:
        """Validate that daily distances are reasonable."""
        issues = []
        daily_distances = []
        
        for i in range(len(locations) - 1):
            loc1 = (locations[i]["lat"], locations[i]["lon"])
            loc2 = (locations[i+1]["lat"], locations[i+1]["lon"])
            
            dist_info = DistanceTool.calculate_distance(loc1, loc2)
            daily_distances.append(dist_info)
            
            if dist_info.get("drive_time_hours", 0) > 4:
                issues.append(f"Day {i+1} to {i+2}: {dist_info['drive_time_hours']:.1f}h drive - too long")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "daily_distances": daily_distances,
            "total_distance": sum(d.get("distance_km", 0) for d in daily_distances)
        }






class TripPlannerAgent:
    """Main agent orchestrator with specialized tools."""
    
    def __init__(self, config: TripConfig):
        self.config = config
        self.llm = OllamaLLM(model=config.model_name, base_url=config.ollama_host)
        
        # Initialize tools
        self.geo_tool = GeolocationTool()
        
        # Create agent tools
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent."""
        return [
            Tool(
                name="geocode_location",
                description="Get accurate coordinates for a location name. Input: location name",
                func=lambda location: json.dumps(
                    self.geo_tool.geocode_location(location, self.config.country)
                )
            ),
            Tool(
                name="calculate_distance",
                description="Calculate distance between two coordinates. Input: 'lat1,lon1,lat2,lon2'",
                func=self._distance_tool_wrapper
            ),
            Tool(
                name="validate_daily_route",
                description="Validate if a route has reasonable daily distances. Input: JSON list of locations with lat/lon",
                func=self._validate_route_wrapper
            )
        ]
    
    def _distance_tool_wrapper(self, coords_str: str) -> str:
        """Wrapper for distance calculation tool."""
        try:
            coords = coords_str.split(',')
            if len(coords) != 4:
                return json.dumps({"error": "Need 4 coordinates: lat1,lon1,lat2,lon2"})
            
            point1 = (float(coords[0]), float(coords[1]))
            point2 = (float(coords[2]), float(coords[3]))
            
            return json.dumps(self.distance_tool.calculate_distance(point1, point2))
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _validate_route_wrapper(self, locations_json: str) -> str:
        """Wrapper for route validation tool."""
        try:
            locations = json.loads(locations_json)
            return json.dumps(self.distance_tool.validate_daily_distances(locations))
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _create_agent(self):
        """Create the main planning agent."""
        prompt = PromptTemplate.from_template("""
You are an expert travel planning agent with access to specialized tools.

Your task: Plan a {duration}-day family road trip in {country}, from {city_start} to {city_end} in {month}.

Family preferences:
- Interests: {interests}
- Budget: {budget}
- Travel with young children
- Prefer nature and cultural sites
- Avoid crowds and long hikes
- Maximum 3 hours driving per day

Use your tools systematically:
1. Build initial trip outline with daily stops
2. Ensure each location is geolocatable
3. Create a final itinerary with verified locations

Always use tools to verify information. Don't make assumptions about coordinates or attractions.

Previous actions: {agent_scratchpad}

Available tools: {tools}
Tool names: {tool_names}

Question: Plan the complete trip itinerary.

Thought: I need to start by understanding the seasonal conditions and then systematically plan the route.
Action:""")
        
        return create_react_agent(self.llm, self.tools, prompt)
    
    def plan_trip(self) -> Dict:
        """Execute the trip planning with agent."""
        query = f"""Plan a {self.config.duration}-day family road trip in {self.config.country} 
                   from {self.config.city_start} to {self.config.city_end} in {self.config.month}.
                   Interests: {', '.join(self.config.interests)}. Budget: {self.config.budget}."""
        
        try:
            result = self.agent_executor.invoke({
                "input": query,
                "duration": self.config.duration,
                "country": self.config.country,
                "city_start": self.config.city_start,
                "city_end": self.config.city_end,
                "month": self.config.month,
                "interests": ', '.join(self.config.interests),
                "budget": self.config.budget
            })
            
            return {
                "success": True,
                "itinerary": result["output"],
                "agent_steps": len(result.get("intermediate_steps", []))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "partial_result": None
            }


class EnhancedTripPlanner:
    """Enhanced trip planner with agent integration."""
    
    def __init__(self, config: TripConfig):
        self.config = config
        self.agent = TripPlannerAgent(config)
    
    def plan_multiple_trips(self, num_iterations: int = 3) -> List[Dict]:
        """Plan multiple trip variations using agents."""
        results = []
        
        for i in range(num_iterations):
            print(f"\n=== Planning Trip Variation {i + 1} ===")
            
            # Vary config slightly for different results
            varied_config = self._vary_config_for_iteration(i)
            agent = TripPlannerAgent(varied_config)
            
            result = agent.plan_trip()
            result["iteration"] = i + 1
            results.append(result)
            
            if result["success"]:
                print(f"✅ Trip {i + 1} planned successfully in {result['agent_steps']} steps")
            else:
                print(f"❌ Trip {i + 1} failed: {result['error']}")
        
        return results
    
    def _vary_config_for_iteration(self, iteration: int) -> TripConfig:
        """Create slight variations in config for different results."""
        config = TripConfig(
            country=self.config.country,
            city_start=self.config.city_start,
            city_end=self.config.city_end,
            duration=self.config.duration,
            month=self.config.month,
            model_name=self.config.model_name,
            ollama_host=self.config.ollama_host
        )
        
        # Vary interests and budget for different perspectives
        interest_variations = [
            ["nature", "culture", "family-friendly"],
            ["adventure", "history", "relaxation"],
            ["photography", "local-food", "museums"],
        ]
        
        budget_variations = ["moderate", "low", "high"]
        
        config.interests = interest_variations[iteration % len(interest_variations)]
        config.budget = budget_variations[iteration % len(budget_variations)]
        
        return config


def main():
    """Main entry point for agent-enhanced trip planner."""
    load_dotenv()
    
    # Create enhanced configuration
    config = TripConfig(
        country=os.getenv("COUNTRY", "Romania"),
        city_start=os.getenv("CITY_START", "Cluj Napoca"),
        city_end=os.getenv("CITY_END", "Cluj Napoca"),
        duration=int(os.getenv("DURATION", "10")),
        month=os.getenv("MONTH", "July"),
        model_name=os.getenv("MODEL_NAME", "llama3"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    
    # Create enhanced planner
    planner = EnhancedTripPlanner(config)
    
    # Plan multiple variations
    num_iterations = 2 # int(os.getenv("NUM_ITERATIONS", "3"))
    results = planner.plan_multiple_trips(num_iterations)
    
    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/agent_trip_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Summary ===")
    successful = sum(1 for r in results if r["success"])
    print(f"Successfully planned {successful}/{len(results)} trip variations")
    print("Results saved to output/agent_trip_results.json")


if __name__ == "__main__":
    main()
