"""Exploracion para clips en la nube: GQL de Twitch, campos de Kick y token del canal de clips. No sube nada."""
import json, os, subprocess, sys, time, urllib.request

def gql(slug):
    q = {'query': 'query($s:ID!){clip(slug:$s){title viewCount durationSeconds videoOffsetSeconds createdAt video{id} game{name}}}',
         'variables': {'s': slug}}
    req = urllib.request.Request('https://gql.twitch.tv/gql', data=json.dumps(q).encode(),
                                 headers={'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko', 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=20))

print('== GQL twitch')
try:
    print(json.dumps(gql('SincereMoldyGaragePartyTime-C2fuK1XJ2UtVfHel'))[:400])
except Exception as e:
    print('GQL FALLO', type(e).__name__, str(e)[:200])

print('== Kick flat (primeros 400)')
t = time.time()
r = subprocess.run(['yt-dlp', '--flat-playlist', '-J', '--impersonate', 'chrome', '--playlist-end', '400', 'https://kick.com/n3on/clips'],
                   capture_output=True, text=True)
e = (json.loads(r.stdout or '{}').get('entries') or [])
print(len(e), 'entradas en', round(time.time() - t), 's')
if e:
    print('campos:', sorted(e[0].keys()))
    for x in e[:3] + e[-2:]:
        print({k: x.get(k) for k in ('title', 'view_count', 'timestamp', 'upload_date', 'duration', 'url')})
print(r.stderr[-400:])

print('== Kick clip completo')
if e:
    r = subprocess.run(['yt-dlp', '-J', '--impersonate', 'chrome', e[0]['url']], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        print({k: j.get(k) for k in ('title', 'view_count', 'timestamp', 'duration', 'width', 'height', 'fps', 'categories', 'tags')})
        print('claves:', sorted(j.keys())[:80])
    except Exception:
        print(r.stderr[-400:])

print('== Kick API clips')
for u in ['https://kick.com/api/v2/channels/n3on/clips?sort=view&time=week', 'https://kick.com/api/v2/clips/' + (e[0]['url'].rstrip('/').split('/')[-1] if e else 'x')]:
    try:
        from curl_cffi import requests as cr
        x = cr.get(u, impersonate='chrome', timeout=30)
        print(u, x.status_code, x.text[:700])
    except Exception as ex:
        print(u, 'FALLO', type(ex).__name__, str(ex)[:200])

print('== Token canal de clips')
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cred = Credentials(None, refresh_token=os.environ['YT_TOKEN_CLIPS'], client_id=os.environ['YT_CLIENT_ID'],
                       client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    yt = build('youtube', 'v3', credentials=cred)
    c = yt.channels().list(part='snippet,contentDetails', mine=True).execute()['items'][0]
    print('canal:', c['snippet']['title'])
    up = c['contentDetails']['relatedPlaylists']['uploads']
    ids = [i['contentDetails']['videoId'] for i in yt.playlistItems().list(part='contentDetails', playlistId=up, maxResults=50).execute().get('items', [])]
    vs = yt.videos().list(part='status', id=','.join(ids)).execute().get('items', []) if ids else []
    print('videos:', len(vs), 'programados:', sorted(v['status'].get('publishAt', '') for v in vs if v['status'].get('publishAt')))
except Exception as ex:
    print('TOKEN FALLO', type(ex).__name__, str(ex)[:300])
