from fastapi import FastAPI
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
        syllables = re.findall(r"[AEIOU]+[^0-9\s]*", phones[0])
        if syllables:
            hyphenated = dic.inserted(word).split("-")
            return stress, hyphenated
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

def detect_meter(text):
    try:
        t = Text(text)
        t.parse()
        return t.bestMeter().label
    except:
        return "unknown"

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    raw_lines = text_input.text.splitlines()
    lines = []
    all_text = []

    rhyme_groups = {}
    for line in raw_lines:
        words_raw = re.findall(r"\b[\w']+\b", line.lower())
        for word in words_raw:
            group = get_rhyme_group(word)
            if group:
                rhyme_groups.setdefault(group, []).append(word)

    for line in raw_lines:
        word_data = []
        for word in line.split():
            clean_word = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_syllables(clean_word)
            rhyme_group = get_rhyme_group(clean_word)

            rhyme_group_id = None
            if rhyme_group and len(rhyme_groups.get(rhyme_group, [])) > 1:
                rhyme_group_id = rhyme_group

            word_data.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_group_id
            })

        lines.append(word_data)
        all_text.append(line)

    meter = detect_meter("\n".join(all_text))
    return {"lines": lines, "meter": meter}
