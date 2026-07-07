import re

def metrics(text: str) -> dict:
    words = re.findall(r"\b\w+\b", text)
    sentences = re.findall(r"[^.!?]+[.!?]", text, flags=re.MULTILINE)
    return {
        "characters": len(text),
        "words": len(words),
        "sentences": len(sentences),
        "average_sentence_words": round(len(words) / len(sentences), 2) if sentences else 0,
    }
