import requests
import subprocess
from os import listdir, makedirs, walk
from os.path import basename, exists, isfile, join, splitext

test_folder = "mp3"
client_id = "AYumMjlCKAs"
acoust_url = 'https://api.acoustid.org/v2/lookup'


def generate_acoustid(f):
    result = subprocess.check_output(['fpcalc', f])
    result = result.strip()
    chroma_result = result.decode('utf-8')
    duration = (chroma_result.split()[0]).split('=')[1]
    fp = chroma_result.split()[1].split('=')[1]
    return (duration, fp)

def get_acoustinfo(f):
    duration, fp = generate_acoustid(f)
    req_data = {
        "client": client_id,
        "meta": "recordings",
        "duration": duration,
        "fingerprint": fp
    }

    res = requests.post(url=acoust_url, params=req_data)
    if res.status_code != 200:
        print('AcoustID failed.\n')
        return '', ''
    music_info = res.json()
    title = music_info['results'][0]['recordings'][0]['title']
    artists = music_info['results'][0]['recordings'][0]['artists']
    return title, artists[0]['name']

# title, artist = get_acoustinfo("Brad-Sucks--Total-Breakdown.mp3")
