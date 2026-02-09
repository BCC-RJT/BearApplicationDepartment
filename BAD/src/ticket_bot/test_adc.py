import google.auth
from googleapiclient.discovery import build

def test_adc():
    try:
        credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.file'])
        service = build('drive', 'v3', credentials=credentials)
        results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        print("✅ ADC Working. Found existing files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
    except Exception as e:
        print(f"❌ ADC Failed: {e}")

if __name__ == '__main__':
    test_adc()
