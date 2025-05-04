from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prosodic import Text
import pronouncing
import re

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze_text(req: TextRequest):
    lines = req.text.strip().split("\n")
    output = []

    for line in lines:
        parsed = Text(line)
        try:
            parsed.parse()
        except Exception:
            output.append([])
            continue

        line_data = []

        for token in parsed.tokens():
            word = token.string
            stress = token.stress()
            syllables = token.syllables()
            syll_strs = [s.string for s in syllables]

            phones = pronouncing.phones_for_word(word.lower())
            rhyme_group = None
            if phones:
                rhyme_group = pronouncing.rhyming_part(phones[0])

            if syll_strs and stress:
                line_data.append({
                    "word": word,
                    "syllables": syll_strs,
                    "stress": stress,
                    "rhymeGroup": rhyme_group
                })
            else:
                line_data.append({
                    "word": word,
                    "syllables": None,
                    "stress": "unknown",
                    "rhymeGroup": None
                })

        output.append(line_data)

    try:
        full_text = Text(req.text)
        full_text.parse()
        meter = full_text.bestMeter().name if full_text.bestMeter() else "free verse"
    except Exception:
        meter = "free verse"

    return {"lines": output, "meter": meter}
