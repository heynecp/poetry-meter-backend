from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen
import re
from collections import Counter

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

METER_PATTERNS = {
    "iambic": "01" * 5,
    "trochaic": "10" * 5,
    "anapestic": "001" * 3,
    "dactylic": "100" * 3,
}

def get_stress_syllables(word):
    phones = pronouncing.phones_for_word(word)
    if phones:
        stress = pronouncing.stresses(phones[0])
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

def detect_meter(line_stresses):
    meter_counts = Counter()
    for stress in line_stresses:
        cleaned = re.sub(r"[^01]", "", stress)
        for meter, pattern in METER_PATTERNS.items():
            if cleaned.startswith(pattern[:len(cleaned)]):
                meter_counts[meter] += 1
    if len(meter_counts) == 0:
        return ["unknown"]
    elif len(meter_counts) > 3:
        return ["mixed"] + [m[0] for m in meter_counts.most_common(3)]
    return [m[0] for m in meter_counts.most_common()]

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    text = text_input.text
    lines_raw = text.split("\n")
    all_stresses = []
    rhyme_groups = {}
    result = []

    words_flat = re.findall(r"\b[\w']+\b", text.lower())
    for word in words_flat:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    for line in lines_raw:
        word_items = []
        words = line.split()
        line_stress = ""
        for word in words:
            clean = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_syllables(clean)
            rhyme = get_rhyme_group(clean)

            if rhyme and len(rhyme_groups.get(rhyme, [])) > 1:
                rhyme_id = rhyme
            else:
                rhyme_id = None

            if stress != "unknown":
                line_stress += stress

            word_items.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_id
            })

        all_stresses.append(line_stress)
        result.append(word_items)

    meters = detect_meter(all_stresses)

    return {
        "lines": result,
        "meters": meters
    }
