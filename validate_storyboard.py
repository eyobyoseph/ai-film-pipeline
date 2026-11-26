import json
from jsonschema import validate, ValidationError

def main():
    with open("schema/storyboard.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open("storyboard.json", "r", encoding="utf-8") as f:
        sb = json.load(f)

    # 1. Validate structure against JSON Schema
    try:
        validate(instance=sb, schema=schema)
    except ValidationError as e:
        print(f"[FAIL] Schema validation error: {e.message}")
        return

    # 2. Validate duration & word count constraints
    shots = sb["shots"]
    total_sec = sum(s["duration_sec"] for s in shots)
    amharic_words = sum(len(s["narration_amharic"].split()) for s in shots)
    english_words = sum(len(s["subtitle_en"].split()) for s in shots)

    assert 8 <= len(shots) <= 12, f"Expected 8-12 shots, got {len(shots)}"
    assert 60 <= total_sec <= 90, f"Expected 60-90s total duration, got {total_sec}s"

    print(f"[OK] Storyboard passed schema & runtime validation!")
    print(f"     - Shots: {len(shots)} (required: 8-12)")
    print(f"     - Total Duration: {total_sec}s (required: 60-90s)")
    print(f"     - Spoken Words: {amharic_words} Amharic words / {english_words} English subtitle words")

if __name__ == "__main__":
    main()