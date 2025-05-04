from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

syllable_dict = pyphen.Pyphen(lang='en')

class RequestBody(BaseModel):
    text: str

def get_stress_pattern(word):
    phones = pronouncing.phones_for_word(word.lower())
    if not phones:
        return "unknown", []

    stresses = pronouncing.stresses(phones[0])
    syllables = syllable_dict.inserted(word).split('-')
    # Pad or trim the stress pattern to match syllables
    stress_list = list(stresses[:len(syllables)] + '0' * (len(syllables) - len(stresses)))
    return stress_list, syllables

def get_rhyme_group(word):
    phones = pronouncing.phones_for_word(word.lower())
    if not phones:
        return None
    rhyming_part = pronouncing.rhyming_part(phones[0])
    return hash(rhyming_part) % 36 if rhyming_part else None

def analyze_line(line):
    words = line.strip().split()
    line_data = []

    for word in words:
        stress, syllables = get_stress_pattern(word)
        line_data.append({
            "word": word,
            "stress": stress,
            "syllables": syllables,
            "rhymeGroup": get_rhyme_group(word)
        })

    return line_data

def guess_meter(lines):
    stress_seq = ""
    for line in lines:
        for token in line:
            if isinstance(token["stress"], list):
                stress_seq += ''.join(token["stress"])
            elif token["stress"] != "unknown":
                stress_seq += token["stress"]
    # Basic heuristic for meter detection
    if "10" in stress_seq or stress_seq.startswith("010"):  # iambic-like
        return "iambic (guessed)"
    elif "01" in stress_seq or stress_seq.startswith("101"):  # trochaic-like
        return "trochaic (guessed)"
    return "free verse"

@app.post("/analyze")
async def analyze_text(body: RequestBody):
    lines = body.text.splitlines()
    result = [analyze_line(line) if line.strip() else [] for line in lines]
    meter_type = guess_meter(result)
    return {"lines": result, "meter": meter_type}
