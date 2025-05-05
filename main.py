#import runs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pronouncing
import pyphen
import string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

##syllable counter
syllable_dict = pyphen.Pyphen(lang='en')

class RequestBody(BaseModel):
    text: str

# Constants
HYBRID_FLAG = "hybrid"

# Helper to clean punctuation
def clean_word(word):
    return word.strip(string.punctuation)

def get_stress_pattern(word):
    phones = pronouncing.phones_for_word(word.lower())
    clean = clean_word(word)
    syllables = syllable_dict.inserted(clean).split('-')

    if not phones:
        # Assign alternating stress if unknown
        default_stress = ["1" if i % 2 == 0 else "0" for i in range(len(syllables))]
        return HYBRID_FLAG, syllables

    stresses = pronouncing.stresses(phones[0])
    stress_list = list(stresses[:len(syllables)] + '0' * (len(syllables) - len(stresses)))
    return stress_list, syllables

def get_rhyme_group(word):
    phones = pronouncing.phones_for_word(word.lower())
    if not phones:
        return None
    rhyming_part = pronouncing.rhyming_part(phones[0])
    return hash(rhyming_part) % 36 if rhyming_part else None

def analyze_line(line):
    words = line.strip().split()
    line_data = []

    for word in words:
        stress, syllables = get_stress_pattern(word)
        if stress == HYBRID_FLAG:
            stress_list = ["2"] * len(syllables)  # 2 = hybrid
        else:
            stress_list = stress

        line_data.append({
            "word": word,
            "stress": stress_list,
            "syllables": syllables,
            "rhymeGroup": get_rhyme_group(word)
        })

    return line_data

def guess_meter(lines):
    stress_seq = ""
    for line in lines:
        for token in line:
            if isinstance(token["stress"], list):
                filtered = [s for s in token["stress"] if s in ("0", "1")]
                stress_seq += ''.join(filtered)

    iambic_count = stress_seq.count("01")
    trochaic_count = stress_seq.count("10")
    dactylic_count = stress_seq.count("100")
    anapestic_count = stress_seq.count("001")

    meter_counts = {
        "iambic": iambic_count,
        "trochaic": trochaic_count,
        "dactylic": dactylic_count,
        "anapestic": anapestic_count,
    }

    sorted_meters = sorted(meter_counts.items(), key=lambda x: -x[1])

    if not stress_seq:
        return "free verse"

    top_meter, count = sorted_meters[0]
    total = sum(meter_counts.values())

    if count / (total or 1) > 0.6:
        return top_meter
    elif len([m for m, c in meter_counts.items() if c > 0]) >= 3:
        return "mixed"
    else:
        return "free verse"

@app.post("/analyze")
async def analyze_text(body: RequestBody):
    lines = body.text.splitlines()
    result = [analyze_line(line) if line.strip() else [] for line in lines]
    meter_type = guess_meter(result)
    return {"lines": result, "meter": meter_type}
