from rag_pipeline import SongRAPTOR
from core.config import RAPTORConfig
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API")

def format_rag_context(results):
    context = ""
    for i, r in enumerate(results):
        context += f"\n### Example {i+1}\n"
        context += r.text.strip() + "\n"
    return context

def build_generation_prompt(query, rag_context):
    return f"""
    You are a lyrics generator.

    User request:
    "{query}"

    Below are style, rythmic patterns and schemes, and thematic examples retrieved from a music database.
    Analyze them for:
    - tone
    - structure
    - vocabulary
    - rhythm
    - pattern
    - themes
    - mood

    DO NOT copy the lyrics.
    Instead, write **original lyrics** inspired by the style.

    --- Retrieved Examples ---
    {rag_context}
    --- END ---

    Now write a NEW set of lyrics inspired by the request and examples.
    Length: 16–24 lines.
    Avoid repeating phrases from the examples. IMPORTANT: Use examples' rhythmic shemes and song structures!
    """

config = RAPTORConfig()
raptor = SongRAPTOR(config)

query = "generate a sad song"
results = raptor.search(query, config.top_k)
formatted_context = format_rag_context(results)
print(formatted_context)
print("\n\n\n\n")

prompt = build_generation_prompt(query, formatted_context)
client = genai.Client(api_key=GOOGLE_API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
)

print(response.text)