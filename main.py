from fastapi import FastAPI
import pronouncing
import os

app = FastAPI()

# Manually download CMU dictionary if missing
if not os.path.exists(pronouncing.DATA_PATH):
    print("Downloading CMU dictionary...")
    pronouncing.download()

@app.get("/stress/{word}")
def get_stress(word: str):
    word = word.lower()
    stresses = pronouncing.stresses(word)
    return {"stress": stresses[0] if stresses else "unknown"}
