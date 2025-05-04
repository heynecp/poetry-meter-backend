from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

dic = pyphen.Pyphen(lang='en')

def get_rhyme_group(word):
    rhymes = pronouncing.rhymes(word)
    if not rhymes:
        return None
    return min([hash(r) % 1000 for r in rhymes])

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    text = data.get("text", "")
    words_raw = re.findall(r"\b[\w']+\b", text.lower())

    result = []
    for word in words_raw:
        phones = pronouncing.phones_for_word(word)
        if phones:
            stresses = pronouncing.stresses(phones[0])
            syllables = dic.inserted(word).split("-")
        else:
            stresses = "unknown"
            syllables = [word]
        result.append({
            "word": word,
            "syllables": syllables,
            "stress": stresses,
            "rhymeGroup": get_rhyme_group(word)
        })
    return { "words": result }
