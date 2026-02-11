import os
import shutil
import boto3
import datetime
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load env variables from project root (../.env)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('BACKUP_BUCKET_NAME')
REGION_NAME = os.getenv('AWS_REGION', 'us-east-1')

DATA_DIR = os.path.join(BASE_DIR, 'data')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups') # Temp local storage

def compress_data():
    """Compresses the data directory into a zip file."""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"bad_backup_{timestamp}"
    
    # Ensure backup dir exists
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    output_path = os.path.join(BACKUP_DIR, archive_name)
    
    print(f"📦 Compressing {DATA_DIR}...")
    shutil.make_archive(output_path, 'zip', DATA_DIR)
    
    return f"{output_path}.zip", f"{archive_name}.zip"

def upload_to_s3(local_file, s3_file):
    """Uploads a file to an S3 bucket."""
    s3 = boto3.client('s3', 
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY,
                      region_name=REGION_NAME)

    try:
        print(f"☁️ Uploading {s3_file} to {BUCKET_NAME}...")
        s3.upload_file(local_file, BUCKET_NAME, s3_file)
        print("✅ Upload Successful")
        return True
    except NoCredentialsError:
        print("❌ Credentials not available")
        return False
    except Exception as e:
        print(f"❌ Upload Failed: {e}")
        return False

def cleanup(local_file):
    """Removes the local backup file."""
    try:
        os.remove(local_file)
        # Also try to remove the backups dir if empty? No, keep it.
        print("🧹 Local backup cleaned up.")
    except Exception as e:
        print(f"⚠️ Error cleaning up: {e}")

def main():
    if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, BUCKET_NAME]):
        print("❌ Error: Missing AWS credentials or Bucket Name in .env")
        return

    local_file, s3_file = compress_data()
    
    if os.path.exists(local_file):
        success = upload_to_s3(local_file, s3_file)
        if success:
           cleanup(local_file)
    else:
        print("❌ Error: Backup file creation failed.")

if __name__ == "__main__":
    main()
