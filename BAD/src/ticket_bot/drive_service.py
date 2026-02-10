import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import os
import datetime

class DriveService:
    def __init__(self, service_account_json_path=None):
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        self.service = None
        
        # Try Service Account File first if provided and exists
        if service_account_json_path and os.path.exists(service_account_json_path):
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    service_account_json_path, scopes=self.scopes)
                self.service = build('drive', 'v3', credentials=self.creds)
                print("✅ Authenticated via Service Account File.")
                return
            except Exception as e:
                print(f"⚠️ Service Account File failed: {e}")

        # Fallback to Application Default Credentials (ADC)
        try:
            print("🔄 Attempting Application Default Credentials (ADC)...")
            self.creds, project = google.auth.default(scopes=self.scopes)
            self.service = build('drive', 'v3', credentials=self.creds)
            print("✅ Authenticated via ADC.")
        except Exception as e:
            print(f"❌ Failed to authenticate Drive Service (both File and ADC failed): {e}")
            self.service = None

    def create_folder(self, folder_name, parent_id=None):
        """Creates a folder and returns its ID."""
        if not self.service: return None
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        try:
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')
        except Exception as e:
            print(f"Error creating folder {folder_name}: {e}")
            return None

    def search_folder(self, folder_name, parent_id=None):
        """Searches for a folder by name."""
        if not self.service: return None
        
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        try:
            results = self.service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            if not items:
                return None
            return items[0]['id']
        except Exception as e:
            print(f"Error searching folder {folder_name}: {e}")
            return None

    def upload_file(self, file_path, file_name, folder_id):
        """Uploads a file to a specific folder."""
        if not self.service: return None
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        
        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except Exception as e:
            print(f"Error uploading file {file_name}: {e}")
            return None

    def upload_ticket_folder(self, ticket_id, user_name, transcript_text, attachment_paths=None):
        """
        Orchestrates the full upload:
        1. Find/Create 'Discord_Tickets/YYYY-MM'
        2. Create '[Ticket-ID]_[Username]'
        3. Upload transcript.txt
        4. Upload attachments
        """
        if not self.service:
            return "⚠️ Drive Upload Skipped: Service not authenticated."

        # Root Folder: Discord_Tickets
        root_id = self.search_folder("Discord_Tickets")
        if not root_id:
            root_id = self.create_folder("Discord_Tickets")
            
        # Month Folder: YYYY-MM
        current_month = datetime.datetime.now().strftime("%Y-%m")
        month_id = self.search_folder(current_month, parent_id=root_id)
        if not month_id:
            month_id = self.create_folder(current_month, parent_id=root_id)
            
        # Ticket Folder
        folder_name = f"{ticket_id}_{user_name}"
        ticket_folder_id = self.create_folder(folder_name, parent_id=month_id)
        
        # Upload Transcript
        # Write to temp file first
        transcript_path = f"transcript_{ticket_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
            
        self.upload_file(transcript_path, "transcript.txt", ticket_folder_id)
        os.remove(transcript_path) # Cleanup
        
        # Upload Attachments
        if attachment_paths:
            for path in attachment_paths:
                if os.path.exists(path):
                    self.upload_file(path, os.path.basename(path), ticket_folder_id)
                    
        # Verification Link
        # Actually returning the folder link would be nice
        return f"https://drive.google.com/drive/folders/{ticket_folder_id}"
