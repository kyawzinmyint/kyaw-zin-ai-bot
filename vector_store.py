import os
import json
import numpy as np
import requests

GEMINI_KEY = open(os.path.expanduser("~/.gemini_key")).read().strip()
EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key=" + GEMINI_KEY
STORE_PATH = os.path.expanduser("~/aiproject/vector_store.json")

def get_embedding(text):
    payload = {"content": {"parts": [{"text": text}]}}
    r = requests.post(EMBED_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
    if r.status_code != 200:
        raise Exception(f"Embed failed: {r.status_code} {r.text[:100]}")
    return r.json()["embedding"]["values"]

def cosine_sim(a, b):
    a = np.array(a); b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

def load_store():
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"texts": [], "vectors": []}

def save_store(store):
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False)

def add_texts(texts):
    store = load_store()
    print(f"Adding {len(texts)} texts...")
    for i, t in enumerate(texts):
        try:
            vec = get_embedding(t)
            store["texts"].append(t)
            store["vectors"].append(vec)
            print(f"  {i+1}/{len(texts)} OK")
        except Exception as e:
            print(f"  {i+1} FAILED: {e}")
    save_store(store)
    print("Saved.")

def search(query, k=5):
    store = load_store()
    if not store["texts"]:
        return []
    qvec = get_embedding(query)
    scores = []
    for i, vec in enumerate(store["vectors"]):
        scores.append((cosine_sim(qvec, vec), store["texts"][i]))
    scores.sort(reverse=True, key=lambda x: x[0])
    return [t for s, t in scores[:k] if s > 0.3]

if __name__ == "__main__":
    kb_path = os.path.expanduser("~/aiproject/knowledge.txt")
    with open(kb_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    add_texts(lines)
    print("\n--- Test Search ---")
    for q in ["မွေးနေ့", "အလုပ်", "Termux"]:
        print(f"\nQuery: {q}")
        for r in search(q, k=3):
            print(f"  - {r}")

