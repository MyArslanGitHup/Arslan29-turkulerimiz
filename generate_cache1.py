import os, json, requests

API_KEY   = os.environ['API_KEY']
FOLDER_ID = os.environ['FOLDER_ID']

def fetch_mp3s(folder_id):
    files, page_token = [], None
    while True:
        params = {
            'q': f"'{folder_id}' in parents and mimeType='audio/mpeg' and trashed=false",
            'fields': 'nextPageToken,files(id,name)',
            'pageSize': 1000,
            'key': API_KEY,
        }
        if page_token:
            params['pageToken'] = page_token
        r = requests.get('https://www.googleapis.com/drive/v3/files', params=params)
        r.raise_for_status()
        data = r.json()
        files.extend(data.get('files', []))
        page_token = data.get('nextPageToken')
        if not page_token:
            break
    return files

def fetch_subfolders(folder_id):
    params = {
        'q': f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        'fields': 'files(id)',
        'pageSize': 100,
        'key': API_KEY,
    }
    r = requests.get('https://www.googleapis.com/drive/v3/files', params=params)
    if not r.ok:
        return []
    return [f['id'] for f in r.json().get('files', [])]

all_files = fetch_mp3s(FOLDER_ID)
for sub_id in fetch_subfolders(FOLDER_ID):
    all_files.extend(fetch_mp3s(sub_id))

tracks = sorted([
    {
        'name': f['name'].replace('.mp3', '').replace('.MP3', ''),
        'id': f['id']
    }
    for f in all_files
], key=lambda x: x['name'].lower())

with open('cache.json', 'w', encoding='utf-8') as fp:
    json.dump({'tracks': tracks, 'count': len(tracks)}, fp, ensure_ascii=False)

print(f"Tamamlandı: {len(tracks)} parça cache.json'a yazıldı.")
