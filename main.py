from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen
import re
from scandroid import Scandroid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dic = pyphen.Pyphen(lang='en_US')
scanner = Scandroid()

class TextInput(BaseModel):
    text: str

def get_stress_syllables(word):
    phones = pronouncing.phones_for_word(word)
    if phones:
        stress = pronouncing.stresses(phones[0])
        syllables = pronouncing.syllable_count(phones[0])
        return stress, pronouncing.phones_for_word(word)[0].split()
    else:
        # fallback syllabification
        parts = dic.inserted(word).split("-")
        return "unknown", parts

def get_rhyme_group(word):
    rhymes = pronouncing.rhymes(word)
    if not rhymes:
        return None
    phones = pronouncing.phones_for_word(word)
    if phones:
        return pronouncing.rhyming_part(phones[0])
    return None

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    original_lines = text_input.text.splitlines()

    # Collect rhyme groups
    flat_words = re.findall(r"\b[\w']+\b", text_input.text.lower())
    rhyme_groups = {}
    for word in flat_words:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    results = []
    meter_counts = {}

    for line in original_lines:
        words_in_line = line.split()
        line_data = []

        for word in words_in_line:
            clean_word = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_syllables(clean_word)
            rhyme_group = get_rhyme_group(clean_word)

            rhyme_group_id = None
            if rhyme_group and len(rhyme_groups.get(rhyme_group, [])) > 1:
                rhyme_group_id = rhyme_group

            line_data.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_group_id
            })

        # Scandroid scan for the line's meter
        scanned = scanner.scan_line(line)
        if scanned and scanned.meter:
            meter_label = scanned.meter.lower()
            meter_counts[meter_label] = meter_counts.get(meter_label, 0) + 1
        else:
            meter_label = "unknown"

        results.append({
            "line": line_data,
            "meter": meter_label
        })

    # Determine dominant meter
    if meter_counts:
        dominant_meter = max(meter_counts.items(), key=lambda x: x[1])[0]
    else:
        dominant_meter = "unknown"

    return {
        "lines": [r["line"] for r in results],
        "detectedMeter": dominant_meter,
        "presentMeters": list(meter_counts.keys())
    }
