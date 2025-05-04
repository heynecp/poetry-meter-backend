from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen
import re
import prosodic

prosodic.config.init()  # Required initialization for prosodic

from prosodic import Text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dic = pyphen.Pyphen(lang='en_US')

class TextInput(BaseModel):
    text: str

def get_stress_syllables(word):
    phones = pronouncing.phones_for_word(word)
    if phones:
        stress = pronouncing.stresses(phones[0])
        syllables = pronouncing.phones_for_word(word)[0].split()
        # fallback to pyphen if syllables aren't available
        parts = dic.inserted(word).split("-")
        return stress, parts
    else:
        parts = dic.inserted(word).split("-")
        return "unknown", parts

def get_rhyme_group(word):
    rhymes = pronouncing.rhymes(word)
    if not rhymes:
        return None
    phones = pronouncing.phones_for_word(word)
    if phones:
        rhyme_part = pronouncing.rhyming_part(phones[0])
        return rhyme_part
    return None

def detect_meter(text: str):
    try:
        t = Text(text)
        t.parse()
        best = t.bestParses()[0]
        return best.meter.name  # e.g., 'iambic', 'trochaic'
    except Exception:
        return "unknown"

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    original_text = text_input.text
    lines_raw = original_text.strip().splitlines()

    response_lines = []
    full_text_for_meter = []

    rhyme_groups = {}
    flat_words = re.findall(r"\b[\w']+\b", text_input.text.lower())
    for word in flat_words:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    for line in lines_raw:
        words_in_line = line.strip().split()
        line_words = []
        for word in words_in_line:
            clean_word = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_syllables(clean_word)
            rhyme_group = get_rhyme_group(clean_word)
            rhyme_group_id = None
            if rhyme_group and len(rhyme_groups.get(rhyme_group, [])) > 1:
                rhyme_group_id = rhyme_group
            line_words.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_group_id
            })
        response_lines.append(line_words)
        full_text_for_meter.append(" ".join([w['word'] for w in line_words]))

    meter_guess = detect_meter("\n".join(full_text_for_meter))

    return {
        "lines": response_lines,
        "meter": meter_guess
    }
