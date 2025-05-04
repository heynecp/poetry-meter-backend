from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pronouncing

app = FastAPI()

# Enable frontend access (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, lock this to your frontend URL
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
        clean_word = ''.join(filter(str.isalpha, word))  # remove punctuation
        stress = pronouncing.stresses(clean_word.lower())
        results.append({
            "word": word,
            "stress": stress[0] if stress else "unknown"
        })

    return { "words": results }
