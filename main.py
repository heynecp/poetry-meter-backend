from fastapi import FastAPI
import pronouncing

app = FastAPI()

@app.get("/stress/{word}")
def get_stress(word: str):
    word = word.lower()
    stresses = pronouncing.stresses(word)
    return {"stress": stresses[0] if stresses else "unknown"}

@app.get("/debug/{word}")
def debug_word(word: str):
    word = word.lower()
    phones = pronouncing.phones_for_word(word)
    stresses = pronouncing.stresses(word)
    return {
        "phones": phones,
        "stress": stresses
    }
