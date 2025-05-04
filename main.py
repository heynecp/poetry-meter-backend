from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prosodic import Text
import pronouncing
import pyphen
import re

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
        syllable_list = dic.inserted(word).split("-")
        return stress, syllable_list
    else:
        return "unknown", dic.inserted(word).split("-")

def get_rhyme_group(word):
    rhymes = pronouncing.rhymes(word)
    if not rhymes:
        return None
    phones = pronouncing.phones_for_word(word)
    if phones:
        rhyme_part = pronouncing.rhyming_part(phones[0])
        return rhyme_part
    return None

def detect_meter(poem_text):
    try:
        t = Text(poem_text)
        t.scan()
        meters = list(set([line.meter.name for line in t.lines if line.meter]))
        if not meters:
            return "unmetered"
        if len(meters) == 1:
            return meters[0]
        else:
            return "mixed (" + ", ".join(meters) + ")"
    except Exception as e:
        print("Meter detection error:", e)
        return "unknown"

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    original_lines = text_input.text.splitlines()
    meter_result = detect_meter(text_input.text)

    all_lines = []

    rhyme_groups = {}
    words_raw = re.findall(r"\b[\w']+\b", text_input.text.lower())
    for word in words_raw:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    for line in original_lines:
        word_objs = []
        for word in line.split():
            clean_word = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_syllables(clean_word)
            rhyme_group = get_rhyme_group(clean_word)

            rhyme_group_id = None
            if rhyme_group and len(rhyme_groups.get(rhyme_group, [])) > 1:
                rhyme_group_id = rhyme_group

            word_objs.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_group_id
            })
        all_lines.append(word_objs)

    return {
        "lines": all_lines,
        "meter": meter_result
    }
