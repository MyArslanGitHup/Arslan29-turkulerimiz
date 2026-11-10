import os, json, requests

API_KEY   = os.environ['API_KEY']
FOLDER_ID = os.environ['FOLDER_ID']

FOLDER_MIME = 'application/vnd.google-apps.folder'


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


def collect_mp3s(folder_id, path=(), visited=None):
    """Klasörü ve TÜM alt klasörlerini (sınırsız derinlik) tarar.
    Her mp3 kaydına bulunduğu klasörün yolunu ('Üst/Alt') ekler.
    Ana klasördeki dosyaların yolu boş ('') olur."""
    if visited is None:
        visited = set()
    if folder_id in visited:
        return []
    visited.add(folder_id)

    mp3s = []
    for item in list_children(folder_id):
        mime = item.get('mimeType', '')
        name = item.get('name', '')
        if mime == FOLDER_MIME:
            # Yol ayırıcısı '/' olduğu için klasör adındaki '/' karakterini değiştir
            safe = name.replace('/', '-').strip() or '(adsız)'
            mp3s.extend(collect_mp3s(item['id'], path + (safe,), visited))
        elif name.lower().endswith('.mp3'):
            # mimeType kontrolüne güvenmiyoruz; uzantı üzerinden yakalıyoruz
            item['folder'] = '/'.join(path)
            mp3s.append(item)
    return mp3s


all_files = collect_mp3s(FOLDER_ID)

# ─── KLASÖRLER ──────────────────────────────────────────────────────────────
# Her klasörün parça sayısı alt klasörlerdekileri de içerir.
folder_counts = {}
for f in all_files:
    parts = f['folder'].split('/') if f['folder'] else []
    for i in range(1, len(parts) + 1):
        p = '/'.join(parts[:i])
        folder_counts[p] = folder_counts.get(p, 0) + 1

folder_paths = sorted(folder_counts, key=lambda p: [s.lower() for s in p.split('/')])
folder_index = {p: i for i, p in enumerate(folder_paths)}
folders = [{'path': p, 'count': folder_counts[p]} for p in folder_paths]

# ─── PARÇALAR ───────────────────────────────────────────────────────────────
# "f": klasör listesindeki index (dosya boyutu küçük kalsın diye yol yerine)
tracks = []
for f in all_files:
    t = {
        'name': f['name'].replace('.mp3', '').replace('.MP3', ''),
        'id': f['id'],
    }
    if f['folder']:
        t['f'] = folder_index[f['folder']]
    tracks.append(t)
tracks.sort(key=lambda x: x['name'].lower())

# "tracks" başta kalmalı: site açılışta dosyanın yalnızca ilk kısmını okuyor
with open('cache.json', 'w', encoding='utf-8') as fp:
    json.dump({'tracks': tracks, 'count': len(tracks), 'folders': folders},
              fp, ensure_ascii=False)

# Klasör listesi site açılır açılmaz gösterilebilsin diye ayrı küçük dosya
with open('folders.json', 'w', encoding='utf-8') as fp:
    json.dump({'folders': folders}, fp, ensure_ascii=False)

print(f"Tamamlandı: {len(tracks)} parça, {len(folders)} klasör yazıldı.")
