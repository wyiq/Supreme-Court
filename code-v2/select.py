#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import os.path, operator
import glob                     # glob.glob
import sys
import shutil       # shutil.rmtree

#shutil.rmtree(dir_path, ignore_errors=True)

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

# the original json dir (which contains both -t01.json & its correspondings
base_dir='1994_2019'
# copy the expected json to the out_dir
out_dir = '1994_2019-sample-936/json'
# the txt file which contains the selected *-t01.json file names
txt_selected = '1994_2019-sample-936.txt'


create_dir(out_dir)

with open(txt_selected) as f:
    for line in f:
        line = line.strip()
        print('process ' + line)
        p1 = os.path.join(base_dir, line)
        p2 = p1[0:-9] + '.json'
        p1_out = os.path.join(out_dir, line)
        p2_out = os.path.join(out_dir, line[0:-9]+'.json')
        shutil.copyfile(p1, p1_out)
        shutil.copyfile(p2, p2_out)

print('done')
