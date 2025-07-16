import os
import time
import json
import requests

# Configuration
GET_URL = "http://104.208.162.61:8083/get"
OUTPUT_FOLDER = "output2"  # Folder to store fetched JSONs
NUM_EMPLOYEES = 20  # Change if you want more/less

# Ensure output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print("📥 Fetching resumes and saving only 'resume' data...\n" + "-" * 50)

for employee_id in range(1, NUM_EMPLOYEES + 1):
    try:
        # POST to /get with employee_id
        response = requests.post(GET_URL, json={
            "employee_id": str(employee_id)
        }, headers={"Content-Type": "application/json"}, timeout=10)

        if response.status_code != 200:
            print(f"❌ ID {employee_id}: HTTP {response.status_code}")
            continue

        data = response.json()
        resume_data = data.get("resume")

        if not resume_data:
            print(f"⚠️ ID {employee_id}: No 'resume' found in response.")
            continue

        # Save only the 'resume' part to file
        output_path = os.path.join(OUTPUT_FOLDER, f"{employee_id}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2)

        print(f"✅ ID {employee_id}: Saved resume to {output_path}")

        # Optional delay for server cooldown
        time.sleep(1)

    except Exception as e:
        print(f"❌ ID {employee_id}: Exception - {e}")

print("\n🎉 Done fetching all resume data.")
