from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uvicorn
import threading
from dotenv import load_dotenv
import os
from google import genai
import logging
from core.models import GenerateRequest, GenerateResponse

# Configure logging
load_dotenv()
GOOGLE_KEY = os.getenv("GEMINI_API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SongRAPTOR API", description="AI-powered song lyrics generation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
raptor = None
models_loaded = False
model_loading_error = None

# Import SongRAPTOR
def initialize_raptor():
    global raptor, models_loaded, model_loading_error
    try:
        from rag_pipeline import SongRAPTOR
        logger.info("Starting model loading in background...")
        raptor = SongRAPTOR()
        models_loaded = True
        logger.info("All models loaded successfully!")
    except Exception as e:
        model_loading_error = str(e)
        logger.error(f"Model loading failed: {e}")
        models_loaded = False

@app.on_event("startup")
async def startup_event():
    # Bind to port immediately, then load models in background
    port = os.environ.get("PORT", 8000)
    logger.info(f"FastAPI server starting on port {port}")
    
    # Start model loading in background thread
    thread = threading.Thread(target=initialize_raptor)
    thread.daemon = True
    thread.start()

# Health check endpoint
@app.get("/health")
async def health_check():
    if not models_loaded and model_loading_error:
        return {
            "status": "degraded", 
            "message": "Server running but models still loading",
            "models_loaded": models_loaded,
            "error": model_loading_error
        }
    elif models_loaded:
        return {
            "status": "healthy",
            "message": "Server running with all models loaded",
            "models_loaded": models_loaded
        }
    else:
        return {
            "status": "loading",
            "message": "Server running, models are still loading",
            "models_loaded": models_loaded
        }

@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')

@app.get("/{path:path}")
async def serve_static(path: str):
    static_path = f"frontend/{path}"
    if os.path.exists(static_path):
        return FileResponse(static_path)
    return FileResponse('frontend/index.html')

@app.post("/generate", response_model=GenerateResponse)
async def generate_lyrics(request: GenerateRequest):
    # Check if models are loaded
    if not models_loaded:
        if model_loading_error:
            raise HTTPException(
                status_code=503, 
                detail=f"Models failed to load: {model_loading_error}. Please check the server logs."
            )
        else:
            raise HTTPException(
                status_code=503, 
                detail="Models are still loading. Please try again in 30-60 seconds."
            )
    
    if not raptor:
        raise HTTPException(status_code=500, detail="RAPTOR not initialized")
    
    try:
        logger.info(f"Generating lyrics for query: {request.query}")
        
        # Search for relevant examples
        results = raptor.search(request.query, request.top_k)
        logger.info(f"Found {len(results)} relevant examples")
        
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
        client = genai.Client(api_key='AIzaSyCWCn6ulx-vRDyHDThaHMxUQfdOWN2GNM0')
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        logger.info("Successfully generated lyrics")
        return GenerateResponse(
            lyrics=response.text,
            context=formatted_context,
            prompt=prompt
        )
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        logger.error(f"Full error details: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)