from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen
import re
import prosodic

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
        syllables = pronouncing.syllable_count(phones[0])
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
        return pronouncing.rhyming_part(phones[0])
    return None

def detect_meter(text):
    prosodic.config['print_to_screen'] = False
    line = prosodic.Text(text)
    line.parse()
    scansion = line.bestParses()[0] if line.bestParses() else ""
    return {
        "scansion": scansion,
        "meter": line.meter().name if line.meter() else "unknown"
    }

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    raw_lines = text_input.text.split("\n")
    all_words = []
    detected_meters = set()

    for raw_line in raw_lines:
        words_raw = re.findall(r"\b[\w']+\b", raw_line.lower())
        rhyme_groups = {}
        for word in words_raw:
            group = get_rhyme_group(word)
            if group:
                rhyme_groups.setdefault(group, []).append(word)

        line_words = []
        for word in raw_line.split():
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

        meter_info = detect_meter(raw_line.strip())
        detected_meters.add(meter_info["meter"])
        all_words.append(line_words)

    return {
        "lines": all_words,
        "detectedMeters": list(detected_meters)
    }
