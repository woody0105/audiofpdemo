import requests
import subprocess
import time
from os import listdir, makedirs, walk
from os.path import basename, exists, isfile, join, splitext

test_folder = "mp3"
client_id = "WqnBlfUPnJ"
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

    tries = 3
    for i in range(tries):
        res = requests.post(url=acoust_url, params=req_data)
        if res.status_code == 200:
            music_info = res.json()
            if len(music_info['results']) == 0 or 'recordings' not in music_info['results'][0]:
                return 'noresult', 'noresult'
            title, artists = None, None
            for recordingsinfo in music_info['results'][0]['recordings']:
                if 'title' in recordingsinfo:
                    title = recordingsinfo['title']
                    artists = recordingsinfo['artists']
                    break
            print("artist:" + artists[0]['name'] + " title:" + title)
            return title, artists[0]['name']
        else:
            print("Bad response from acoustid api, retrying in 1 second...")
            time.sleep(1)
            continue

    return None, None



