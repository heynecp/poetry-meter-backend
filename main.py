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

def get_stress_and_syllables(word):
    phones = pronouncing.phones_for_word(word)
    if phones:
        stress = pronouncing.stresses(phones[0])
        syllables = dic.inserted(word).split('-')
        return stress, syllables
    else:
        fallback = dic.inserted(word).split('-')
        return "unknown", fallback

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
    raw_lines = text_input.text.strip().split('\n')
    all_words = re.findall(r"\b[\w']+\b", text_input.text.lower())
    rhyme_groups = {}

    for word in all_words:
        group = get_rhyme_group(word)
        if group:
            rhyme_groups.setdefault(group, []).append(word)

    structured_lines = []
    prosody_obj = Text(text_input.text)
    prosody_obj.parse()

    meter_type = prosody_obj.bestMeter().name if prosody_obj.bestMeter() else "free verse"

    for line in raw_lines:
        words = line.strip().split()
        line_result = []

        for word in words:
            clean_word = re.sub(r"[^\w']", '', word).lower()
            stress, syllables = get_stress_and_syllables(clean_word)
            rhyme_group = get_rhyme_group(clean_word)

            rhyme_id = rhyme_group if rhyme_group and len(rhyme_groups[rhyme_group]) > 1 else None

            line_result.append({
                "word": word,
                "stress": stress,
                "syllables": syllables,
                "rhymeGroup": rhyme_id
            })

        structured_lines.append(line_result)

    return {"meter": meter_type if meter_type else "free verse", "lines": structured_lines}
