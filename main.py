from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
        return stress, pronouncing.syllable_list(phones[0])
    else:
        # fallback
        parts = dic.inserted(word).split("-")
        return "unknown", parts

def get_rhyme_group(word):
    rhymes = pronouncing.rhymes(word)
    if not rhymes:
        return None
    # normalize by finding rhyme sound suffix from phones
    phones = pronouncing.phones_for_word(word)
    if phones:
        rhyme_part = pronouncing.rhyming_part(phones[0])
        return rhyme_part
    return None

@app.post("/analyze")
async def analyze_text(text_input: TextInput):
    words_raw = re.findall(r"\b[\w']+\b", text_input.text.lower())
    
    rhyme_groups = {}
    for word in words_raw:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    words = []
    for word in text_input.text.split():
        clean_word = re.sub(r"[^\w']", '', word).lower()
        stress, syllables = get_stress_syllables(clean_word)
        rhyme_group = get_rhyme_group(clean_word)

        # Only return rhyme group if there's a pair
        rhyme_group_id = None
        if rhyme_group and len(rhyme_groups.get(rhyme_group, [])) > 1:
            rhyme_group_id = rhyme_group

        words.append({
            "word": word,
            "stress": stress,
            "syllables": syllables,
            "rhymeGroup": rhyme_group_id
        })

    return {"words": words}
