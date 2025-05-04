from fastapi import FastAPI
import pronouncing

app = FastAPI()

@app.get("/stress/{word}")
def get_stress(word: str):
    word = word.lower()
    stresses = pronouncing.stresses(word)

    # Return full array of options if needed for debugging
    return {"stress": stresses[0] if stresses else "unknown"}
