from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from rag_pipeline import SongRAPTOR
from core.models import GenerateRequest, GenerateResponse
from google import genai
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API")

app = FastAPI(title="SongRAPTOR API", description="AI-powered song lyrics generation")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files
@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

@app.get("/{path:path}")
async def serve_static(path: str):
    static_path = f"frontend/{path}"
    if os.path.exists(static_path):
        return FileResponse(static_path)
    return FileResponse('frontend/index.html')

raptor = None

@app.on_event("startup")
async def startup_event():
    global raptor
    try:
        # Initialize RAPTOR without building index (uses existing ChromaDB)
        raptor = SongRAPTOR()
        print("SongRAPTOR initialized with existing ChromaDB database")

    except Exception as e:
        print(f"Error during startup: {e}")
        raptor = SongRAPTOR()

@app.post("/generate", response_model=GenerateResponse)
async def generate_lyrics(request: GenerateRequest):
    if not raptor:
        raise HTTPException(status_code=500, detail="RAPTOR not initialized")
    
    try:
        # Search for relevant examples
        results = raptor.search(request.query, request.top_k)
        
        # Format context
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

            Below are style, rhythmic patterns and schemes, and thematic examples retrieved from a music database.
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
            Avoid repeating phrases from the examples. IMPORTANT: Use examples' rhythmic schemes and song structures!
            """

        formatted_context = format_rag_context(results)
        prompt = build_generation_prompt(request.query, formatted_context)
        
        # Generate lyrics using Gemini
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return GenerateResponse(
            lyrics=response.text,
            context=formatted_context,
            prompt=prompt
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

# Serve frontend in production
if os.path.exists("../frontend"):
    app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)