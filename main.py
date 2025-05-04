from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pronouncing

app = FastAPI()

# Allow frontend (React) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open to all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_text(request: Request):
    data = await request.json()
    text = data.get("text", "")
    words = text.strip().split()

    results = []
    for word in words:
        lowered = word.lower()
        stresses = pronouncing.stresses(lowered)
        results.append({
            "word": word,
            "stress": stresses[0] if stresses else "unknown"
        })

    return {"words": results}
