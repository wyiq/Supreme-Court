#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

from pydub import AudioSegment
from parselmouth.praat import run_file
import os, os.path  # os.path.sep
import sys          # sys.exit
import json         # json.load
import shutil       # shutil.rmtree
import requests     # requests.get
import glob         # glob.glob
import operator 
import csv          # csv.writer
import time


# get the current directory of the script
cur_dir_path = os.path.dirname(os.path.realpath(__file__))

# !!! UPDATE THE DIRECTORY FOR YOUR CASES !!!
sample_dir="1994_2019/sample-936/"
# store the splited mp3 files for each speaker
output_dir = os.path.join(cur_dir_path, sample_dir + 'splitted_mp3')
# store the downloaded mp3 file (to cache the downloaded mp3 file)
mp3_folder = os.path.join(cur_dir_path, sample_dir + 'mp3')
# eg: processing all xx-t01.json: json/*-t01.json
json_patten_in_batch = os.path.join(cur_dir_path, sample_dir + 'json/*-t01.json')

##### split mp3 start #####

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
        if sections is None:
            return None
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
        if meta['media_file'] is None:
            return None
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

# split_mp3 for a single speaker's sound
def process_speaker(speakerTurns, sound):
    result = None
    for turn in speakerTurns:
        start, stop = turn[0] * 1000, turn[1] * 1000
        if result is None:
            result = sound[start:stop]
        else:
            result = result + sound[start:stop]
    return result

def process_speaker_1st_turn(speakerTurns, sound):
    turn = speakerTurns[0]
    start, stop = turn[0] * 1000, turn[1] * 1000
    return sound[start:stop]

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

# split_mp3 for a single json file
def split_mp3(json_file):
    print ('Processing json file:', json_file)
    mp3_url = get_mp3_url(json_file)
    if mp3_url is None:
        print("No mp3 url found!")
        return None
    print ('mp3 url is:', mp3_url)
    mp3_file = download_mp3(mp3_url)
    print ('mp3 file is:', mp3_file)

    # prepare for the output folder
    filename = os.path.basename(json_file)
    filename_without_ext = os.path.splitext(filename)[0]
    cur_output_dir = os.path.join(output_dir, filename_without_ext)
    create_dir(cur_output_dir)

    speakerMap = get_speakers_map(json_file)
    if speakerMap is None:
        return None
    sound = load_sound_from_mp3(mp3_file)
    top1, top2 = None, None
    for key in speakerMap:
        sub_sound = process_speaker(speakerMap[key], sound)
        cur_output_path = os.path.join(cur_output_dir, key + '.mp3')
        if top1 is None or len(top1[0]) < len(sub_sound):
            top2 = top1
            top1 = [sub_sound, key]
        elif top2 is None or len(top2[0]) < len(sub_sound):
            top2 = [sub_sound, key]
        # save_to_mp3(cur_output_path, sub_sound)
    # only store the first turn
    top1[0] = process_speaker_1st_turn(speakerMap[top1[1]], sound)
    top2[0] = process_speaker_1st_turn(speakerMap[top2[1]], sound)
    save_to_mp3(os.path.join(cur_output_dir, top1[1] + '.mp3'), top1[0])
    save_to_mp3(os.path.join(cur_output_dir, top2[1] + '.mp3'), top2[0])
    return top1[1], top2[1]
    

# split_mp3 for multiple json files by given the file pattens
def split_in_batch(json_path_pat):
    # step 1. split mp3 and obtain meta json
    meta_jsons = []
    jsons = glob.glob(json_path_pat)
    count, total = 1, len(jsons)
    failCount, failedJson = 0, []
    for json_file in jsons:
        print('\n{0}/{1} processing {2}'.format(count, total, json_file))
        try:
            filename = os.path.basename(json_file)
            filename_without_ext = os.path.splitext(filename)[0]
            cur_output_dir = os.path.join(output_dir, filename_without_ext)
            if os.path.exists(cur_output_dir):
                print("Already processed, skip...")
                count += 1
                continue

            res = split_mp3(json_file)
            if res is None:
                failCount += 1
                failedJson.append(json_file)
                count += 1
                continue
            print(res)
            meta_json = json_file[0:-9] + '.json'
            print ('Construct meta:', meta_json)
            meta_jsons.append(meta_json)
        except:
            print("failed for", json_file)
            import traceback
            traceback.print_exc()
        count += 1
    print('Over! processed:', total, 'json files', failCount, 'failed!')
    if failCount > 0:
        print('\nFailed json file(s):')
        print('------')
        for json_file in failedJson:
            print(json_file)


##### split mp3 end #####

def main():
    create_dir(output_dir, False)
    create_dir(mp3_folder, False)

    if len(os.sys.argv) > 1: # split_mp3 single file
        split_mp3(os.sys.argv[1])
    else: # batch mode
        split_in_batch(json_patten_in_batch)
    print('Done')

if __name__ == '__main__':
    start_time = time.time()
    main()
    elapsed_time = (time.time() - start_time)

    if elapsed_time > 100:
        elapsed_min = elapsed_time / 60
        print("--- Spliting takes %s minutes ---" % round(elapsed_min, 1))
    else:
        print("--- Spliting takes %s seconds ---" % round(elapsed_time, 1))
