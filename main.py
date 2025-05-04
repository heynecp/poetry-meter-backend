from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prosodic import Text
import pronouncing
import pyphen

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

dic = pyphen.Pyphen(lang='en')

class RequestBody(BaseModel):
    text: str

def analyze_line(line):
    if not line.strip():
        return []

    try:
        parsed = Text(txt=line)
        parsed.parse()
    except Exception as e:
        print(f"Prosodic failed on line: {line!r} with error: {e}")
        return [{"word": line.strip(), "stress": "unknown"}]

    line_data = []
    for token in parsed.tokens():
        word_text = token.string
        stress = token.stress()
        syllables = dic.inserted(word_text).split('-') if word_text else []

        line_data.append({
            "word": word_text,
            "stress": stress,
            "syllables": syllables,
            "rhymeGroup": get_rhyme_group(word_text)
        })

    return line_data

def get_rhyme_group(word):
    phones = pronouncing.phones_for_word(word.lower())
    if not phones:
        return None
    rhyming_part = pronouncing.rhyming_part(phones[0])
    return hash(rhyming_part) % 36 if rhyming_part else None

@app.post("/analyze")
async def analyze_text(body: RequestBody):
    lines = body.text.splitlines()
    result = [analyze_line(line) for line in lines if line.strip()]

    # Flatten all lines to check for overall meter
    flat_text = ' '.join(body.text.splitlines()).strip()
    try:
        overall = Text(txt=flat_text)
        overall.parse()
        meter_type = overall.bestMeter().name if overall.bestMeter() else "free verse"
    except Exception as e:
        print(f"Failed to determine meter: {e}")
        meter_type = "free verse"

    return {"lines": result, "meter": meter_type}
