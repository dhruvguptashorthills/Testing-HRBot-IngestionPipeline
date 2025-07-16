import os
import requests
import time
import pandas as pd

# Configuration
UPLOAD_URL = "http://104.208.162.61:8083/upload2"
RESUME_FOLDER = "data"  # Folder with input resumes

# Supported extensions
SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx"}

# Get sorted list of resume files (to ensure 1-20 mapping is consistent)
resume_files = sorted(
    [f for f in os.listdir(RESUME_FOLDER) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
)

timesheet = []

for idx, filename in enumerate(resume_files[:15], 1):  # Up to 20 resumes
    employee_id = str(idx)  # Assign employee ID 1 to 20
    file_path = os.path.join(RESUME_FOLDER, filename)
    _, ext = os.path.splitext(filename)
    new_filename = f"{employee_id}{ext}"

    print(f"Uploading {filename} as employee_id={employee_id} (sent as {new_filename})")

    start_time = time.time()
    status = "Success"
    error_msg = ""
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()

        files = {
            "file": (new_filename, file_data),  # Use employee_id as filename
        }
        data = {
            "employee_id": employee_id,
        }

        response = requests.post(UPLOAD_URL, files=files, data=data, timeout=None)  # Infinite timeout

        if response.status_code == 200:
            print(f"✅ Uploaded {filename} as {new_filename}")
        else:
            status = f"Failed ({response.status_code})"
            error_msg = response.text
            print(f"❌ Failed to upload {filename}: {response.status_code}\n{response.text}")

    except requests.RequestException as e:
        status = "Error"
        error_msg = str(e)
        print(f"❌ Error uploading {filename}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    timesheet.append({
        "employee_id": employee_id,
        "filename": filename,
        "new_filename": new_filename,
        "status": status,
        "error_message": error_msg,
        "time_taken_sec": round(duration, 2)
    })

print("\n🎉 All resume uploads completed.")

# Save timesheet to Excel
df = pd.DataFrame(timesheet)
excel_path = "upload_timesheet.xlsx"
df.to_excel(excel_path, index=False)
print(f"📝 Timesheet saved to {excel_path}")