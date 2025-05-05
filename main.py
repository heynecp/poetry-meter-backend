#import runs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import pronouncing
import pyphen
import string
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# syllable counter
syllable_dict = pyphen.Pyphen(lang='en')

class RequestBody(BaseModel):
    text: str
    customStresses: Dict[str, List[str]] = {}

# Constants
HYBRID_FLAG = "hybrid"

# Helper to clean punctuation and normalize
def clean_word(word):
    word = re.sub(r'[\u2019\u2018]', "'", word)  # Normalize smart quotes
    word = re.sub(r'[\u2014\u2013]', "--", word)  # Normalize em/en dash
    return word.strip(string.punctuation).lower()

def get_stress_pattern(word, customStresses):
    cleaned = clean_word(word)
    if cleaned in customStresses:
        return customStresses[cleaned], syllable_dict.inserted(cleaned).split('-')

    phones = pronouncing.phones_for_word(cleaned)
    syllables = syllable_dict.inserted(cleaned).split('-')

    if not phones:
        default_stress = ["1" if i % 2 == 0 else "0" for i in range(len(syllables))]
        return HYBRID_FLAG, syllables

    stresses = pronouncing.stresses(phones[0])
    stress_list = list(stresses[:len(syllables)] + '0' * (len(syllables) - len(stresses)))
    return stress_list, syllables

def get_rhyme_group(word):
    phones = pronouncing.phones_for_word(word.lower())
    if not phones:
        return None
    rhyming_part = pronouncing.rhyming_part(phones[0])
    return hash(rhyming_part) % 36 if rhyming_part else None

def analyze_line(line, customStresses):
    words = line.strip().split()
    line_data = []

    for word in words:
        stress, syllables = get_stress_pattern(word, customStresses)
        if stress == HYBRID_FLAG:
            stress_list = ["2"] * len(syllables)  # 2 = hybrid
        else:
            stress_list = stress

        line_data.append({
            "word": word,
            "stress": stress_list,
            "syllables": syllables,
            "rhymeGroup": get_rhyme_group(word)
        })

    return line_data

def guess_meter(lines):
    stress_seq = ""
    for line in lines:
        for token in line:
            if isinstance(token["stress"], list):
                filtered = [s for s in token["stress"] if s in ("0", "1")]
                stress_seq += ''.join(filtered)

    iambic_count = stress_seq.count("01")
    trochaic_count = stress_seq.count("10")
    dactylic_count = stress_seq.count("100")
    anapestic_count = stress_seq.count("001")

    meter_counts = {
        "iambic": iambic_count,
        "trochaic": trochaic_count,
        "dactylic": dactylic_count,
        "anapestic": anapestic_count,
    }

    sorted_meters = sorted(meter_counts.items(), key=lambda x: -x[1])

    if not stress_seq:
        return "free verse"

    top_meter, count = sorted_meters[0]
    total = sum(meter_counts.values())

    if count / (total or 1) > 0.6:
        return top_meter
    elif len([m for m, c in meter_counts.items() if c > 0]) >= 3:
        return "mixed"
    else:
        return "free verse"

@app.post("/analyze")
async def analyze_text(body: RequestBody):
    lines = body.text.splitlines()
    result = [analyze_line(line, body.customStresses) if line.strip() else [] for line in lines]
    meter_type = guess_meter(result)
    return {"lines": result, "meter": meter_type}
