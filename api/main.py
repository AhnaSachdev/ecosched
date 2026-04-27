import requests
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class Prompt(BaseModel):
    text: str

# ✅ ADD THIS
@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/ask")
def ask_gemini(prompt: Prompt):
    try:
        # 🔌 Mock electricity data (temporary)
        electricity_data = {
            "zone": "IN-NO",
            "carbonIntensity": 420  # example value
        }

        # 🧠 Combine with user input
        full_prompt = f"""
        You are EcoSched AI.

        Current carbon intensity in {electricity_data['zone']} is {electricity_data['carbonIntensity']} gCO2/kWh.

        Lower values = cleaner electricity.
        Higher values = more pollution.

        Based on this, answer the user's question:

        {prompt.text}
        """

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(full_prompt)

        return {"response": response.text}

    except Exception as e:
        return {"error": str(e)}
@app.get("/test-electricity")
def test_electricity():
    try:
        url = "https://api.electricitymaps.com/v3/carbon-intensity/latest"

        headers = {
            "auth-token": os.getenv("ELECTRICITY_MAPS_API_KEY")
        }

        params = {
            "zone": os.getenv("ELECTRICITY_MAPS_ZONE")
        }

        res = requests.get(url, headers=headers, params=params)

        return res.json()

    except Exception as e:
        return {"error": str(e)}