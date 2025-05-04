from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen
import re
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
        syllables = re.split(r'[\d]', phones[0])
        if not syllables or syllables == ['']:
            parts = dic.inserted(word).split("-")
            return stress, parts
        return stress, dic.inserted(word).split("-")
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

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    lines_raw = text_input.text.strip().splitlines()
    rhyme_groups = {}
    all_words = re.findall(r"\b[\w']+\b", text_input.text.lower())

    for word in all_words:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    lines = []
    for line in lines_raw:
        words_in_line = []
        for word in line.split():
            clean_word = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_syllables(clean_word)
            rhyme_group = get_rhyme_group(clean_word)

            rhyme_group_id = None
            if rhyme_group and len(rhyme_groups.get(rhyme_group, [])) > 1:
                rhyme_group_id = rhyme_group

            words_in_line.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_group_id
            })
        lines.append(words_in_line)

    try:
        prosody_obj = Text(text_input.text)
        prosody_obj.parse()
        meter = prosody_obj.bestMeter
        meter_type = meter.name if meter else "free verse"
    except Exception:
        meter_type = "free verse"

    return {"lines": lines, "meter": meter_type}
