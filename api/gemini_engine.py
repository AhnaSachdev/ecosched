import google.generativeai as genai
import json, os, time, logging
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

PROMPT_TEMPLATE = """
You are EcoSched, an OS resource scheduler that optimizes for both
carbon efficiency and CPU throughput simultaneously.

Job telemetry:
  job_name:         {job_name}
  cpu_burst_pct:    {cpu_burst_pct}    (current CPU usage %)
  io_wait_pct:      {io_wait_pct}      (% time CPU idle waiting for I/O)
  mem_pressure_mb:  {mem_pressure_mb}  (swap used in MB)
  carbon_intensity: {carbon_ci} gCO2/kWh
  urgency:          {urgency}/5        (5=critical real-time, 1=batch)
  deadline_seconds: {deadline_seconds} (seconds until hard deadline)
  current_state:    {current_state}

Decision rules (apply in priority order):
1. NEVER defer if deadline_seconds < 90 regardless of carbon
2. NEVER defer if urgency >= 4 (customer-facing workloads)
3. If io_wait_pct > 65, prefer throttle or defer even if carbon is clean
4. If mem_pressure_mb > 300 and current_state == "deferred", set action="run"
5. If carbon_ci > 400 and cpu_burst_pct > 30 and urgency < 3: defer
6. If carbon_ci < 150: run
7. If 150 <= carbon_ci <= 400: throttle medium-urgency jobs

Estimate co2_saved_grams: (cpu_burst_pct/100) * 0.3 * (carbon_ci/1000) * 120

Respond with ONLY valid JSON:
{{"action":"run|throttle|defer","defer_score":0.0-1.0,
  "co2_saved_grams":float,"reasoning":"one sentence max 15 words",
  "resume_in_seconds":null_or_int}}
"""

def _rule_based_fallback(payload: dict):
    io_wait = payload["io_wait_pct"]
    carbon = payload["carbon_ci"]
    urgency = payload["urgency"]
    deadline = payload["deadline_seconds"]
    cpu = payload["cpu_burst_pct"]

    # Rule 1 & 2 (highest priority)
    if deadline < 90 or urgency >= 4:
        return {
            "action": "run",
            "defer_score": 0.0,
            "co2_saved_grams": 0,
            "reasoning": "Critical job — cannot defer",
            "resume_in_seconds": None
        }

    # Rule 3 (IO wait)
    if io_wait > 65:
        return {
            "action": "throttle",
            "defer_score": 0.6,
            "co2_saved_grams": 5,
            "reasoning": "High IO wait — freeing CPU helps throughput",
            "resume_in_seconds": None
        }

    # Rule 5 (carbon high)
    if carbon > 400 and cpu > 30 and urgency < 3:
        return {
            "action": "defer",
            "defer_score": 0.8,
            "co2_saved_grams": 10,
            "reasoning": "High carbon — delaying reduces emissions",
            "resume_in_seconds": 120
        }

    # Default
    return {
        "action": "run",
        "defer_score": 0.0,
        "co2_saved_grams": 0,
        "reasoning": "Default fallback",
        "resume_in_seconds": None
    }

async def decide(payload: dict) -> dict:
    prompt = PROMPT_TEMPLATE.format(**payload)
    start_time = time.time()

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=200,
                temperature=0.1
            )
        )

        elapsed = (time.time() - start_time) * 1000
        if elapsed > 50:
            logging.warning(f"Gemini took {elapsed:.0f}ms — over 50ms budget")

        text = response.text.strip()

        # Remove markdown if present
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]
            if text.startswith("json"):
                text = text[4:]

        # Extract JSON safely
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            text = text[start:end]
            return json.loads(text)
        except Exception:
            logging.error(f"Raw Gemini output: {text}")
            return _rule_based_fallback(payload)

    except Exception as e:
        logging.error(f"Gemini error: {e}")
        return _rule_based_fallback(payload)
    