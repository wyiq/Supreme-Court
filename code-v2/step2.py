#!/usr/bin/env python
# -*- encoding:utf-8 -*-

from parselmouth.praat import run_file
import os, os.path, operator
import glob                     # glob.glob
import json                     # json.load
import csv                      # csv.writer
import time
import re

cur_dir_path = os.path.dirname(os.path.realpath(__file__))

# !!! UPDATE THE DIRECTORY FOR YOUR CASES !!!
praat_path = os.path.join(cur_dir_path, "myspsolution.praat")
textgrid_out_dir = os.path.join(cur_dir_path, "tmp/")
sample_dir = os.path.join(cur_dir_path, "1994_2019/sample-936")
splitted_mp3_dir = sample_dir + "/splitted_mp3/"
meta_json_dir = sample_dir + "/json"

# This stores the target csv file
csv_out_path = sample_dir + "/result.csv"

# This file records the process status and failure reason
csv_fail_out_path = sample_dir + "/fail.csv"

# This file is used to indicate whether all the jsons have been processed
status_path = os.path.join(cur_dir_path, "status.txt")

# const values
STR_APPELLANT = "appellant"
STR_APPELLEE = "appellee"
STR_UNKNOWN = "unknown"
CSV_HEADERS = ['SeqNo', 'ID', 'Appellant', 'Petitioner Gender', 'Appellee', 'Respondent Gender', 'Petitioner f0_std', 'Respondent f0_std', 'Petitioner f0_mean', 'Respondent f0_mean']


# Obtain the std and mean of a sound (myspf0sd, myspf0mean)
# refs: https://github.com/Shahabks/my-voice-analysis
def myspf0sd(sound_path):
    print('processing myspf0sd for file:', sound_path)
    try:
        objects = run_file(praat_path, -20, 2, 0.3, "yes",sound_path, textgrid_out_dir, 80, 400, 0.01, capture_output=True)
        z1 = str(objects[1]) 
        z2 = z1.strip().split()
        std = float(z2[8])
        mean = float(z2[7])
    except:
        std = 0
        e = sys.exc_info()[0]
        print('[error]', e)
        print ("[TODO] The sound of the audio was not clear:", sound_path)
        raise ValueError
    return std, mean


# Obtain all the json files whose file name doesn't contain "-t01" string
def obtain_meta_jsons(json_dir):
    meta_jsons = set(glob.glob(os.path.join(json_dir, '*.json'))) - set(glob.glob(os.path.join(json_dir, '*-t01.json')))
    res_jsons = list(meta_jsons)
    res_jsons.sort()
    return res_jsons

# Parse the meta json file and analysis each advocate
# json file ends with -t01.json
def get_advocate_map(json_file):
    # {identifier: petitioner/ petitionee / unkown}
    advocateMap = {}
    lastNameMap = {}
    with open(json_file) as f:
        meta = json.load(f)

        if 'advocates' not in meta:
            print('No advocates info in json file:', json_file)
            raise
        for adv in meta['advocates']:
            id = adv['advocate']['identifier']
            lastName = adv['advocate']['last_name']
            lastNameMap[id] = re.sub(r'\W+', '', lastName)
            # advocate description is missing
            if 'advocate_description' not in adv:
                advocateMap[id] = STR_UNKNOWN
            else:
                desciption = adv['advocate_description'].lower()
                if desciption.find('appellant') > -1 or desciption.find('petitioner') > -1:
                    advocateMap[id] = STR_APPELLANT
                elif desciption.find('appellee') > -1 or desciption.find('respondent') > -1:
                    advocateMap[id] = STR_APPELLEE
                else:
                    advocateMap[id] = STR_UNKNOWN
    return advocateMap, lastNameMap

# json_file not ends with -t01.json
def get_speaker_gender_map(json_file, names):
    print('get gender map for file:', json_file)
    print('names:', names)
    genderMap = {}
    with open(json_file) as f:
        meta = json.load(f)
        sections = meta['transcript']['sections']
        for section in sections:
            for turn in section['turns']:
                if turn['text_blocks'] is None:
                    continue
                for txtBlock in turn['text_blocks']:
                    for name in names:
                        if name not in genderMap:
                            txt = txtBlock['text']
                            if re.search('Mr\. [\w ]*?' + name, txt): # male
                                genderMap[name] = 'M'
                            elif re.search('Ms\. [\w ]*?' + name, txt) or \
                                 re.search('Mrs\. [\w ]*?' + name, txt): # female
                                genderMap[name] = 'F'
                    if len(genderMap) == len(names):
                        return genderMap
    return genderMap

# get the filename without extension
def get_filename_without_ext(fullpath):
    filename = fullpath.split(os.path.sep)[-1]
    filename_without_ext = os.path.splitext(filename)[0]
    return filename_without_ext

def load_from_csv(filename):
    res = {}
    if not os.path.exists(filename):
        return res
    with open(filename, 'r') as f:
        # creating a csv writer object
        lines = f.readlines()
        lines = lines[1:]  # remove header
        for line in lines:
            id = line.split(',')[1]
            res[id] = True
            
    return res

# writing to csv file
def save_to_csv(filename, fields, rows):
    head = True
    if os.path.exists(filename):
        head = False
    with open(filename, 'a') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the fields
        if head:
            csvwriter.writerow(fields)
        # writing the data rows
        csvwriter.writerows(rows)

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
# the json file must be without "-t01.json" suffix
def process(json_file):
    print ('Processing file: ', json_file)
    advocateMap, lastNameMap = get_advocate_map(json_file)

    if len(set(advocateMap.values())) == 1:
        return None, 'Can not detect appellant or appellee correctly.' 
    # print('Obtain advocate map: ', advocateMap)
    sound_json = json_file[0:-5] + '-t01.json'
    genderMap = get_speaker_gender_map(sound_json, set(lastNameMap.values()))
    # if len(genderMap) < len(advocateMap):
    #     return None, 'Can not detect the gender correctly.'

    filename_without_ext = get_filename_without_ext(json_file)
    mp3_out_dir = os.path.join(splitted_mp3_dir, filename_without_ext + "-t01")

    # list the files and get the largest two files
    all_files = (os.path.join(basedir, filename) for basedir, dirs, files in os.walk(mp3_out_dir) for filename in files)
    if all_files is None:
        return None, 'mp3 file has error'
    csv_out = [filename_without_ext, '', '', '', '', -1, -1, -1, -1]
    fail_reason = 'Unkown reason'
    for mp3_file in all_files:
        std, mean = myspf0sd(mp3_file)
        id = get_filename_without_ext(mp3_file)
        print ('{0:24s} : {1:9s} : std = {2}, mean = {3}'.format(id, advocateMap[id], std, mean))
        if lastNameMap[id] in genderMap:
            gender = genderMap[lastNameMap[id]]
        else:
            gender = 'X'
        if advocateMap[id] == STR_APPELLANT:
            csv_out[1] = id
            csv_out[2] = gender
            csv_out[5] = std
            csv_out[7] = mean
        elif advocateMap[id] == STR_APPELLEE:
            csv_out[3] = id
            csv_out[4] = gender
            csv_out[6] = std
            csv_out[8] = mean
        else:
            print ('[Error] Advocate ', id, 'not exist in json file:', json_file)
            fail_reason = '[Error] Advocate ' + id + ' not exist in json file:' + json_file
            return None, fail_reason

    return csv_out, fail_reason

# process for multiple json files by given the json dir
def process_in_batch(json_dir):
    json_files = obtain_meta_jsons(json_dir)

    failCount = 0
    failedJson = []
    csv_rows = []
    csv_done = load_from_csv(csv_out_path)
    csv_fail = load_from_csv(csv_fail_out_path)
    count, total = 1, len(json_files)
    for json_file in json_files:
        print('\n{0}/{1} processing {2}'.format(count, total, json_file))
        filename_without_ext = get_filename_without_ext(json_file)
        if filename_without_ext in csv_done:
            print('skip! already processed!')
            count += 1
            continue
        if filename_without_ext in csv_fail:
            print('skip! already processed failed!')
            count += 1
            continue
        fail_reason = 'Unknown reason'
        success = True
        seq_str = '{}/{}'.format(count, total)
        try:
            save_to_csv(csv_fail_out_path, CSV_HEADERS, [(seq_str, filename_without_ext, 'processing...')])
            csv_row, fail_reason = process(json_file)
            if csv_row is not None:
                csv_rows.append(csv_row)
                csv_row.insert(0, seq_str)
                save_to_csv(csv_out_path, CSV_HEADERS, [csv_row])
            else:
                success = False
        except:
            success = False
            import traceback
            traceback.print_exc()

        if not success:
            failCount += 1
            failedJson.append(json_file)
            save_to_csv(csv_fail_out_path, CSV_HEADERS, [(seq_str, filename_without_ext, fail_reason)])
        print('Success\n' if success else 'Failed\n')
        count += 1

    print ('CSV file is saved to:', csv_out_path)
    print ('Total {0} json files processed, {1} json file(s) failed.'.format(len(json_files), failCount))
    if failCount > 0:
        print('\nFailed json file(s):')
        print('------')
        for json_file in failedJson:
            print(json_file)

def write_status():
    with open(status_path, 'w') as f:
        f.write('success\n')
def reset_status():
    if os.path.exists(status_path):
        os.remove(status_path)

def main():
    create_dir(textgrid_out_dir, False)

    if len(os.sys.argv) > 1: # process single file
        res = process(os.sys.argv[1])
        print(','.join(CSV_HEADERS))
        print(','.join([str(e) for e in res]))
    else: # batch mode
        # eg. put all your json files under dir json/
        process_in_batch(meta_json_dir)
    print('\nDone')

if __name__ == '__main__':
    reset_status()
    start_time = time.time()
    main()
    elapsed_time = (time.time() - start_time)
    if elapsed_time > 100:
        elapsed_min = elapsed_time / 60
        print("--- Processing takes %s minutes ---" % round(elapsed_min, 1))
    else:
        print("--- Processing takes %s seconds ---" % round(elapsed_time, 1))
    write_status()
