import os, json, requests

API_KEY   = os.environ['API_KEY']
FOLDER_ID = os.environ['FOLDER_ID']

def list_children(folder_id):
    """Bir klasörün altındaki tüm dosya ve klasörleri (sayfalama dahil) döndürür."""
    items, page_token = [], None
    while True:
        params = {
            'q': f"'{folder_id}' in parents and trashed=false",
            'fields': 'nextPageToken,files(id,name,mimeType)',
            'pageSize': 1000,
            'key': API_KEY,
        }
        if page_token:
            params['pageToken'] = page_token
        r = requests.get('https://www.googleapis.com/drive/v3/files', params=params)
        r.raise_for_status()
        data = r.json()
        items.extend(data.get('files', []))
        page_token = data.get('nextPageToken')
        if not page_token:
            break
    return items

def collect_mp3s(folder_id, visited=None):
    """Klasörü ve TÜM alt klasörlerini (sınırsız derinlik) tarayıp mp3 dosyalarını toplar."""
    if visited is None:
        visited = set()
    if folder_id in visited:
        return []
    visited.add(folder_id)

    mp3s = []
    for item in list_children(folder_id):
        mime = item.get('mimeType', '')
        name = item.get('name', '')
        if mime == 'application/vnd.google-apps.folder':
            mp3s.extend(collect_mp3s(item['id'], visited))
        elif name.lower().endswith('.mp3'):
            # mimeType kontrolüne güvenmiyoruz; uzantı üzerinden yakalıyoruz
            mp3s.append(item)
    return mp3s

all_files = collect_mp3s(FOLDER_ID)

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
