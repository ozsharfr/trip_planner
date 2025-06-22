
# 🗺️ Travel Itinerary Generator

This is an interactive travel planning tool powered by a language model (LLM) and a simple Streamlit UI.  
It generates a multi-day itinerary and map based on your preferences, including country, travel style, trip duration, and more.

---

## 📦 Requirements

- Python 3.8 or higher
- Recommended: VS Code or any IDE with terminal support

### Python packages

Install required dependencies:

```bash
pip install streamlit openai geopy
```

---

## 🚀 How to Run

### 1. Clone the repository or place the code files in a folder.
### 1a. Make sure to have an API key for Groq llm, otherwise , select your own LLM with respective API and apply in main code

### 2. Run the app using Python:

```bash
python -m streamlit run streamlit_app.py
```

> ⚠️ If `streamlit` is not recognized, use the command above instead of `streamlit run ...`.

---

## 🧾 What It Does

The app:
1. Lets you input travel parameters (start city, duration, preferences, etc.).
2. Sends a prompt to a language model to generate a route.
3. Extracts the locations and coordinates.
4. Displays an interactive map with the suggested route.

---

## 📋 Input Parameters

The app will ask you for:
- **Country** – The country of travel
- **Start / End City** – Trip starting and ending locations
- **Trip Composition** – E.g., Solo, Family, Couple, etc.
- **Trip Duration** – Number of days
- **Max Distance Per Day** – Travel pacing
- **Month** – Travel time for weather/seasonal context
- **Preferences** – Choose from:
  - Nature
  - Culture
  - Relaxation
  - Adventure
  - etc..

---

## 📍 Output

- A dynamic map (`map_<id>.html`) will be generated.
- The map will also appear embedded inside the Streamlit app.

---

## 🛠️ Notes

- You may need to replace or configure the LLM backend (`main_plan_prompt`) using OpenAI or another provider.
- If using `.env` previously, this app now takes user inputs via UI instead.

---

## 🧑‍💻 Dev Tips

- Prompt templates are built in `_get_trip_prompt_template()`
- The file `main.py` contains the main planning logic
- `streamlit_app.py` is the app entry point
- Coordinates are extracted and validated using `geopy`

---
