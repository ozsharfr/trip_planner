
import time
from geopy.geocoders import Nominatim
from langchain.prompts import PromptTemplate
from extract_coordinates import get_coordinates_from_query, extract_coords_from_llm_result
from validate_locations_coords import detect_coords_with_llm, query_coordinates_from_name, validate_location

### Optional : Consider using an agent to validate and improve the trip plan 
def try_agent(result , llm_model):
     # Turn the list into a string or formatted input for the agent
    agent_input = f"""Here is a list of locations from a trip plan:
    {result}

    Your task: Validate the coordinates for each location. 
    If a location has invalid coordinates or is ambiguous, try to correct it using geopy or fallback to the LLM.
    Return the cleaned list with reliable 'lat' and 'lon' values for each location.
    """

    from langchain.agents import initialize_agent, Tool
    from langchain.agents.agent_types import AgentType
    from langchain.tools import tool

    @tool
    def geopy_lookup(name: str) -> tuple:
        """Use geopy to look up coordinates of a place."""
        geo = Nominatim(user_agent="trip_planner", timeout=100).geocode(name)
        if geo:
            return (geo.latitude, geo.longitude)
        return (None, None)

    @tool
    def llm_coord_fallback(name: str) -> tuple:
        """Use LLM to estimate coordinates of a location."""
        return detect_coords_with_llm(query=name, llm=llm_model)

    @tool
    def rerun_single_day(day_number: int ,llm_model) -> list:
        """Re-plan just one day using LLM with refined prompt."""

        prompt_template = PromptTemplate(
        input_variables=["day,number", "result"],
        template=
        """You are a highly reliable georgarph.\n
        Can you Re-plan day {day_number} with less ambigous location?  
        Current locations : {result}
        Answer must be in this pattern, where both 'lat' and 'lon' are mentioned:  (lat : float, lon :float), or None if no reliable answer found
        """
        )
        
        llm_chain = prompt_template | llm_model | (lambda result : get_coordinates_from_query(result))

        input_data = {"result": result, "day_number": day_number}
        result_day = llm_chain.invoke(input_data)

        return result_day

    tools = [
        Tool(name="GeopyLookup", func=geopy_lookup, description="Get lat/lon from geopy"),
        Tool(name="LLMFallback", func=llm_coord_fallback, description="Guess coordinates via LLM"),
        Tool(name="RerunDay", func=rerun_single_day, description="Fix or replan a problematic day")
    ]

    agent = initialize_agent(tools=tools, llm=llm_model, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

    # Use agent to process each location
    t = time.time()
    improved_locations = agent.run(agent_input)
    print (f"Time taken for agent processing: {time.time() - t:.2f} seconds")
    return improved_locations