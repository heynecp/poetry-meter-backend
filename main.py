from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pronouncing

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_text(request: Request):
    data = await request.json()
    text = data.get("text", "")
    words = text.strip().split()

    result = []
    rhyme_dict = {}
    rhyme_group_counter = 0

    for word in words:
        # Clean up punctuation (keep apostrophes if desired)
        clean_word = ''.join(filter(str.isalpha, word.lower()))
        stresses = pronouncing.stresses(clean_word)
        rhymes = pronouncing.rhymes(clean_word)

        # Find rhyme group if any
        rhyme_group = None
        for rh in rhymes:
            if rh in rhyme_dict:
                rhyme_group = rhyme_dict[rh]
                break

        # If none assigned yet, assign new group
        if rhymes and rhyme_group is None:
            rhyme_group = rhyme_group_counter
            for rh in rhymes:
                rhyme_dict[rh] = rhyme_group
            rhyme_group_counter += 1

        result.append({
            "word": word,
            "stress": stresses[0] if stresses else "unknown",
            "rhymeGroup": rhyme_group if rhyme_group is not None else None
        })

    return { "words": result }
