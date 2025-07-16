import os
import json
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Paths
GROUND_TRUTH_FOLDER = "ground_truth"
OUTPUT1_FOLDER = "output1"
OUTPUT2_FOLDER = "output2"
NUM_EMPLOYEES = 20

# Output files
EXCEL_GT = "match_vs_ground_truth.xlsx"
EXCEL_REGRESSION = "output1_vs_output2.xlsx"

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Field weights
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

# Semantic similarity for strings
def semantic_similarity(a, b):
    if not a or not b:
        return 0.0
    emb1 = model.encode(a, convert_to_tensor=True)
    emb2 = model.encode(b, convert_to_tensor=True)
    return float(util.cos_sim(emb1, emb2).item())

# Semantic similarity for lists
def list_semantic_overlap(list1, list2):
    if not list1:
        return 1.0 if not list2 else 0.0
    if not list2:
        return 0.0

    norm1 = [json.dumps(i, sort_keys=True) if isinstance(i, dict) else str(i) for i in list1]
    norm2 = [json.dumps(i, sort_keys=True) if isinstance(i, dict) else str(i) for i in list2]

    embeddings1 = model.encode(norm1, convert_to_tensor=True)
    embeddings2 = model.encode(norm2, convert_to_tensor=True)

    scores = []
    for emb in embeddings1:
        sim_scores = util.cos_sim(emb, embeddings2)
        max_sim = float(sim_scores.max().item())
        scores.append(max_sim)

    return round(np.mean(scores), 4)

# Field comparison
def score_field(gt, test):
    if (not gt or gt == "") and (not test or test == ""):
        return 1.0
    if isinstance(gt, str) and isinstance(test, str):
        return semantic_similarity(gt, test)
    elif isinstance(gt, list) and isinstance(test, list):
        return list_semantic_overlap(gt, test)
    return 0.0

# Full comparison for each resume
def compute_field_scores(gt_data, test_data):
    scores = {}
    for field in WEIGHTS:
        gt_val = gt_data.get(field, "")
        test_val = test_data.get(field, "")
        field_score = score_field(gt_val, test_val)
        scores[field] = round(field_score * 100, 2)
    return scores

# Generic comparison function
def run_comparison(folder1, folder2, output_excel, label1, label2):
    rows = []
    print(f"\n🔍 Comparing {label1} vs {label2}...")

    for i in range(1, NUM_EMPLOYEES + 1):
        file1 = os.path.join(folder1, f"{i}.json")
        file2 = os.path.join(folder2, f"{i}.json")

        try:
            with open(file1, "r", encoding="utf-8") as f1:
                data1 = json.load(f1)
            with open(file2, "r", encoding="utf-8") as f2:
                data2 = json.load(f2)

            res1 = data1.get("resume", data1)
            res2 = data2.get("resume", data2)

            field_scores = compute_field_scores(res1, res2)
            total_weight = sum(WEIGHTS.values())
            weighted_score = sum(field_scores[f] * WEIGHTS[f] for f in WEIGHTS) / total_weight

            row = {"ID": i, **field_scores, "Overall Score": round(weighted_score, 2)}
            rows.append(row)

            print(f"✅ ID {i}: {round(weighted_score, 2)}% match")

        except Exception as e:
            print(f"❌ ID {i}: Error - {e}")

    df = pd.DataFrame(rows)
    df.to_excel(output_excel, index=False)
    print(f"📁 Report saved to: {output_excel}")

# Run both comparisons
run_comparison(GROUND_TRUTH_FOLDER, OUTPUT1_FOLDER, EXCEL_GT, "Ground Truth", "Output1")
run_comparison(OUTPUT1_FOLDER, OUTPUT2_FOLDER, EXCEL_REGRESSION, "Output1", "Output2")
