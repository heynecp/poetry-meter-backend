from fastapi import FastAPI, Request
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

def get_stress_syllables(word):
    phones = pronouncing.phones_for_word(word)
    if phones:
        stress = pronouncing.stresses(phones[0])
        syllables = dic.inserted(word).split("-")
        return stress, syllables
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

def detect_meter_from_stress(stress_seq):
    meter_patterns = {
        'iambic': ['01', '0101', '010101'],
        'trochaic': ['10', '1010'],
        'anapestic': ['001', '001001'],
        'dactylic': ['100', '100100']
    }
    detected = []
    for name, patterns in meter_patterns.items():
        for pattern in patterns:
            if stress_seq.startswith(pattern):
                detected.append(name)
                break
    return detected[0] if detected else None

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    lines_raw = text_input.text.splitlines()
    words_raw = re.findall(r"\b[\w']+\b", text_input.text.lower())

    rhyme_groups = {}
    for word in words_raw:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    result_lines = []
    all_stress_sequences = []

    for line in lines_raw:
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

            if stress != "unknown":
                all_stress_sequences.append(stress)

        result_lines.append(word_data)

    stress_seq_flat = ''.join(all_stress_sequences)
    detected = [detect_meter_from_stress(stress_seq_flat[i:i+6]) for i in range(0, len(stress_seq_flat), 6)]
    top_meters = [m for m, _ in Counter(filter(None, detected)).most_common(3)]
    if len(top_meters) > 3:
        top_meters = ['mixed'] + top_meters

    return { "lines": result_lines, "meters": top_meters }
