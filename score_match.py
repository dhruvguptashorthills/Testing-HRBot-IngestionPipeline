import os
import json
import pandas as pd
from collections import Counter
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Config paths
NIFI_FOLDER = "output1"
GROUND_TRUTH_FOLDER = "ground_truth"
NUM_EMPLOYEES = 15
OUTPUT_EXCEL = "resume_match_scores.xlsx"

# Load semantic similarity model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Semantic similarity between two strings
def semantic_similarity(a, b):
    if not a or not b:
        return 0.0
    emb1 = model.encode(a, convert_to_tensor=True)
    emb2 = model.encode(b, convert_to_tensor=True)
    return float(util.cos_sim(emb1, emb2).item())

# Semantic overlap for lists
def list_semantic_overlap(list1, list2):
    if not list1:
        return 1.0 if not list2 else 0.0
    if not list2:
        return 0.0

    # Normalize to strings
    norm1 = [json.dumps(i, sort_keys=True) if isinstance(i, dict) else str(i) for i in list1]
    norm2 = [json.dumps(i, sort_keys=True) if isinstance(i, dict) else str(i) for i in list2]

    # Encode in batch
    embeddings1 = model.encode(norm1, convert_to_tensor=True)
    embeddings2 = model.encode(norm2, convert_to_tensor=True)

    # Match each item from GT with best from NiFi
    scores = []
    for emb in embeddings1:
        sim_scores = util.cos_sim(emb, embeddings2)
        max_sim = float(sim_scores.max().item())
        scores.append(max_sim)

    return round(np.mean(scores), 4)

# Weights for each field
WEIGHTS = {
    "name": 10,
    "email": 10,
    "phone": 10,
    "summary": 5,
    "education": 20,
    "experience": 20,
    "skills": 10,
    "projects": 10,
    "certifications": 5
}

def score_field(gt, nifi):
    # Case: both empty → 100% match
    if (not gt or gt == "") and (not nifi or nifi == ""):
        return 1.0

    if isinstance(gt, str) and isinstance(nifi, str):
        return semantic_similarity(gt, nifi)
    elif isinstance(gt, list) and isinstance(nifi, list):
        return list_semantic_overlap(gt, nifi)
    return 0.0


# Compute field-wise scores
def compute_field_scores(gt_data, nifi_data):
    scores = {}
    for field in WEIGHTS:
        gt_val = gt_data.get(field, "")
        nifi_val = nifi_data.get(field, "")
        field_score = score_field(gt_val, nifi_val)
        scores[field] = round(field_score * 100, 2)
    return scores

# Main logic
rows = []

print("📊 Calculating semantic match scores...")

for i in range(1, NUM_EMPLOYEES + 1):
    gt_path = os.path.join(GROUND_TRUTH_FOLDER, f"{i}.json")
    nifi_path = os.path.join(NIFI_FOLDER, f"{i}.json")

    try:
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_json = json.load(f)

        with open(nifi_path, "r", encoding="utf-8") as f:
            nifi_json = json.load(f)

        gt_resume = gt_json.get("resume", gt_json)
        nifi_resume = nifi_json.get("resume", nifi_json)

        field_scores = compute_field_scores(gt_resume, nifi_resume)
        total_weight = sum(WEIGHTS.values())
        weighted_score = sum((field_scores[f] * WEIGHTS[f]) for f in WEIGHTS) / total_weight

        row = {"ID": i, **field_scores, "Overall Score": round(weighted_score, 2)}
        rows.append(row)

        print(f"✅ ID {i}: {round(weighted_score, 2)}%")

    except Exception as e:
        print(f"❌ ID {i}: Error - {e}")

# Save results to Excel
df = pd.DataFrame(rows)
df.to_excel(OUTPUT_EXCEL, index=False)
print(f"\n📁 Excel report saved to: {OUTPUT_EXCEL}")
