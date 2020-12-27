import os
import subprocess

def resampe_file(fname):
	fname_new = os.path.join("resampled/", fname) 
	subprocess.call('ffmpeg -i "' + fname + '" -ar 44100 "' + fname_new +'"', shell=True)


def resample_directory(dir_name):
	directory = './'
	for root, dirs, files in os.walk(directory):
	    for file in files:
	        if file.endswith('.mp3'):
	            resampe_file(file)

if __name__ == '__main__':
	resample_directory("./")