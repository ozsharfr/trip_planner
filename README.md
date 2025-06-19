
### LLM-based Trip Planner

This project is an automated **LLM-based travel planner** that generates a multi-day road trip tailored to your preferences. It uses a language model (via Ollama) to plan locations, validates and fixes coordinates, and renders an interactive map using Folium.

---

#### Features

- 🔮 Generates trip plans using a local LLM (via Groq)
- 📍 Validates location coordinates with geopy and fallback LLM
- 🧹 Filters out geographic outliers and invalid entries
- 🗺️ Produces interactive maps with clustered markers and routes
- 🧠 Optional LangChain Agent to refine ambiguous results

---

#### Project Structure

```bash
trip_planner/
├── trip_planner.py                 # Main entry point
├── config.py                       # Loads environment variables
├── extract_coordinates.py          # Parses and sanitizes LLM outputs
├── prompt_trip.py                  # Trip planning prompts and LLM calls
├── remove_problemtaic_coords.py    # Outlier filtering logic
├── map.py                          # Folium map generation
├── agent_trip.py                   # Optional LangChain agent tools
├── output/                         # Generated maps and location CSVs
└── .env                            # User-defined trip config
```

---

#### Requirements

- Python 3.8+
- Groq (Add it's API key)
- Required Python packages:


pip install -r requirements.txt
---

#### Setup

1. **Create a `.env` file** with the model key and trip parameters:

```env
GROQ_API_KEY=YOUR-KEY-HERE
COUNTRY=Bulgaria
CITY_START=Sofia
CITY_END=Varna
DURATION=10
MONTH=July
COMPOSITION=a family with young children
...

```

---

#### Run the Planner

```bash
python main.py
```

This will:
- Generate a trip plan for the given settings
- Fix any coordinate or geolocation issues
- Save the map to: `output/trip_map_0.html`, `output/locations0.csv`, etc.

---

#### Optional: Use Agent for Validation

You can enable a LangChain agent that uses tools like:
- `geopy_lookup`: for real coordinate lookups
- `llm_coord_fallback`: for LLM-based correction
- `rerun_single_day`: re-generates problematic days

Uncomment this in `main()` to use:
```python
# locations_w_agent = try_agent(locations, llm_model)
```

---

#### Example Output

![screenshot](output/Screenshot.png)

- **Blue markers** = trip days
- **Red line** = driving route
- Output CSV includes lat/lon and names per day

---
