from BAD.src import db
import os

# Initialize
print("Initializing DB...")
db.init_db()

# Add a mock result
job_id = "TEST-JOB-001"
url = "https://drive.google.com/file/d/test-file-id/view"
print(f"Adding result for {job_id}...")
row_id = db.add_result(job_id, url, "pdf_statement")
print(f"Result added with Row ID: {row_id}")

# Query it back
print(f"Querying result for {job_id}...")
res = db.get_latest_result(job_id)
if res:
    print("SUCCESS: Found result:")
    print(f"  Job ID: {res['job_id']}")
    print(f"  URL: {res['file_url']}")
    print(f"  Type: {res['result_type']}")
else:
    print("FAILURE: No result found.")
