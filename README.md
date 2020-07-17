# Supreme-Court
A Python Function Separate Supreme Court's Oral Arguments Audio File 

This document is a work in progress.

This function will be able to:

1. Automatically download supreme court's oral arguments audio file in `.mp3` format from `.json` file obtained from Oyez.org's API.
2. Separate the `.mp3` file into small pieces according to timestamp information from the `.json` file.
3. Merge cutted pieces into separate `.mp3` files based on speaker.
4. Organize all speakers' `.mp3` file from the same case into the same folder and name the folder as docket number.

See `example` for details. 

## Installation

Installing this function is easy, but don't forget to install ffmpeg/pydub 

```
git clone https://github.com/wyiq/Supreme-Court.git
```

This function requires following Python libraries. 

```
sudo pip3 install pydub 
```
```
brew install ffmpeg
```

## Quickstart

Process for multiple json files by given the file pattens

```
import main as main
cur_dir_path = os.path.dirname(os.path.realpath("main.py"))
main.process_in_batch(cur_dir_path + "/*-t01.json")
```
