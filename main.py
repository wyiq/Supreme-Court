#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

from pydub import AudioSegment
import os, os.path  # os.path.sep
import sys          # sys.exit
import json         # json.load
import shutil       # shutil.rmtree
import requests     # requests.get
import glob         # glob.glob

# get the current directory of the script
cur_dir_path = os.path.dirname(os.path.realpath(__file__))

# !!! UPDATE THE DIRECTORY FOR YOUR CASES !!!
# store the splited mp3 files for each speaker
output_dir = cur_dir_path + '/out'
# store the downloaded mp3 file (to cache the downloaded mp3 file)
mp3_folder = cur_dir_path + '/mp3'

# To download a mp3 file by given the URL of it (skip if already exists)
# return the local file path.
def download_mp3(url):
    filename = url.split('/')[-1]
    filepath = os.path.join(mp3_folder, str(filename))
    if os.path.exists(filepath): # mp3 file already exists, skip download
        print ('Skip to download mp3 from web, it already exists')
        return filepath
    r = requests.get(url)
    with open(filepath, 'wb') as fd:
        fd.write(r.content)
    return filepath

# Parse the json file and analysis each speakers turns
def get_speakers_map(json_file):
    speakerMap = {}
    with open(json_file) as f:
        meta = json.load(f)
        sections = meta['transcript']['sections']
        for section in sections:
            for turn in section['turns']:
                start = turn['start']
                stop = turn['stop']
                if turn['speaker'] is None:
                    continue
                id = turn['speaker']['identifier']
                if not id in speakerMap:
                    speakerMap[id] = []
                speakerMap[id].append((start, stop))
    return speakerMap

# Parse the mp3 url from the json file
def get_mp3_url(json_file):
    with open(json_file) as f:
        meta = json.load(f)
        for media in meta['media_file']:
            if media['mime'] == 'audio/mpeg':
                return str(media['href'])
    return None

# Load the sound from mp3 file
def load_sound_from_mp3(filepath):
    return AudioSegment.from_mp3(filepath)

# Save a sound to the mp3 file
def save_to_mp3(filepath, sound):
    sound.export(filepath, format="mp3")

# process for a single speaker's sound
def process_speaker(speakerTurns, sound):
    result = None
    for turn in speakerTurns:
        start, stop = turn[0] * 1000, turn[1] * 1000
        if result is None:
            result = sound[start:stop]
        else:
            result = result + sound[start:stop]
    return result

# create the directory, if force_empty is true, it will
# delete the existing directory
def create_dir(dir_path, force_empty=True):
    if os.path.exists(dir_path):
        if force_empty:
            shutil.rmtree(dir_path, ignore_errors=True)
        else:
            return
    try:
        os.mkdir(dir_path)
    except:
        print('Failed to create directory: ', dir_path)
        sys.exit(-1)

# process for a single json file
def process(json_file):
    print ('Processing json file:', json_file)
    mp3_url = get_mp3_url(json_file)
    print ('mp3 url is:', mp3_url)
    mp3_file = download_mp3(mp3_url)
    print ('mp3 file is:', mp3_file)

    # prepare for the output folder
    filename = os.path.basename(json_file)
    filename_without_ext = os.path.splitext(filename)[0]
    cur_output_dir = os.path.join(output_dir, filename_without_ext)
    create_dir(cur_output_dir)

    speakerMap = get_speakers_map(json_file)
    sound = load_sound_from_mp3(mp3_file)
    for key in speakerMap:
        sub_sound = process_speaker(speakerMap[key], sound)
        cur_output_path = os.path.join(cur_output_dir, key + '.mp3')
        save_to_mp3(cur_output_path, sub_sound)

# process for multiple json files by given the file pattens
def process_in_batch(json_path_pat):
    for json_file in glob.glob(json_path_pat):
        process(json_file)


if __name__ == '__main__':
    create_dir(output_dir)
    create_dir(mp3_folder, False)

    if len(os.sys.argv) > 1: # process single file
        process(os.sys.argv[1])
    else: # batch mode
        # eg: processing all xx-t01.json: json/*-t01.json
        process_in_batch('json/*.json')
    print('Done')
