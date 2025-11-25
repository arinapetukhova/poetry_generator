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

raptor = None

def initialize_raptor():
    global raptor
    try:
        from rag_pipeline import SongRAPTOR
        raptor = SongRAPTOR()
        logger.info("App successfully started!")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")

@app.on_event("startup")
async def startup_event():

    port = os.environ.get("PORT", 8000)
    logger.info(f"FastAPI server starting on port {port}")
    
    thread = threading.Thread(target=initialize_raptor)
    thread.daemon = True
    thread.start()


@app.get("/health")
async def health_check():
    if not raptor:
       return {
            "status": "healthy",
            "message": "Server running correctly"
        }
    else:
        return {
            "status": "loading",
            "message": "RAPTOR wasn't initialized"
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
    if not raptor:
        raise HTTPException(status_code=500, detail="RAPTOR not initialized")
    
    try:
        logger.info(f"Generating lyrics for query: {request.query}")
        
        results = raptor.search(request.query, request.top_k)
        logger.info(f"Found {len(results)} relevant examples")
        
        def format_rag_context(results):
            context = ""
            for i, r in enumerate(results):
                context += f"\n### Example {i+1}\n"
                context += r.text.strip() + "\n"
            return context

        def build_generation_prompt(query, rag_context):
            return f"""
                You are a professional lyrics generator.

                USER REQUEST: {query}

                MUSICAL EXAMPLES AND STYLE REFERENCES:
                {rag_context}

                INSTRUCTIONS:
                - Analyze the musical examples for tone, structure, vocabulary, rhythm, patterns, themes, and mood
                - Create COMPLETELY ORIGINAL lyrics - DO NOT copy phrases or lines
                - Match the musical style, rhyme schemes, and structure from the examples
                - Write 16-24 lines with proper song structure (verses, chorus, bridge, outro)
                - Focus on the emotional tone, rhythmic patterns, and rhyme schemes

                OUTPUT FORMAT:
                Reasoning: [Your analysis of the examples (according to instructions) and how you'll approach the lyrics]

                Generated Lyrics:
                """

        formatted_context = format_rag_context(results)
        prompt = build_generation_prompt(request.query, formatted_context)
        
        client = genai.Client(api_key=GOOGLE_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        response_text = response.text

        reasoning = ""
        lyrics = ""
        if "Reasoning:" in response_text and "Generated Lyrics:" in response_text:
            parts = response_text.split("Generated Lyrics:", 1)
            reasoning = parts[0].replace("Reasoning:", "").strip()
            lyrics = parts[1].strip()
        else:
            lyrics = response_text

        logger.info("Successfully generated lyrics")
        return GenerateResponse(
            lyrics=lyrics,
            reasoning=reasoning,
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