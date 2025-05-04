from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prosodic import Text
import pronouncing

app = FastAPI()

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
            tokens = parsed.tokens if isinstance(parsed.tokens, list) else parsed.tokens()
        except Exception:
            output.append([])
            continue

        line_data = []

        for token in tokens:
            word = token.string
            stress = token.stress()
            syllables = token.syllables()
            syll_strs = [s.string for s in syllables] if syllables else []

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

    # Determine overall meter
    try:
        full = Text(req.text)
        full.parse()
        meter = full.bestMeter().name if full.bestMeter() else "free verse"
    except Exception:
        meter = "free verse"

    return {"lines": output, "meter": meter}
