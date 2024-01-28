## Last update 2024-01-27 by Noah Macey.
## This script searches through time-aligned transcriptions with corresponding .wav files and extracts
## audio excerpts that contain certain words. It is designed to be used in conjunction with OpenAI's 
## Whisper, an automated transcription tool. I used it to process over 500 hours of podcast audio as part
## of a sociolinguistic project, and it greatly speeds up the process of finding specific
## variables (i.e., words) in large a large corpus of audio.
 
## For the script to work, the audio files must each have a corresponding tsv that is identically
## named except for the extension. Each tsv should have three columns: the first and second should
## contain the timestamps in milliseconds, and the third column should contain the utterance. This
## is the default format exported by Whisper. 

## The audio excerpts are saved in a separate directory. Each has its own unique identifier; the 
## metadata for each excerpt will be written to output.tsv in the same directory as the script. 

## This repository is set up as an example. Running the code should search for the terms in word_list.txt
## within /audio_data/ and return corresponding excerpts and an output.tsv. You can try changing the 
## items in word_list.txt. The example audio are podcast episodes from the Ezra Klein Show. 

## ****If you run the script multiple times, it is advisable to delete the /audio_excerpts/ directory before rerunning the script.****

import os, csv, wave
from pathlib import Path

# Variables to set:
PATH_TO_WAVS = Path.cwd() / "audio_data" # Path to the directory containing the wav files and their corresponding tsv transcripts.
TARGET_WORD_LIST = Path.cwd() / "word_list.txt" # Path to the txt files containing the target words. The utterances containing these words will be extracted from all the wavs in PATH_TO_WAVS. The txt file should contain one word per line. 
PATH_TO_OUTPUT_TSV = Path.cwd() / "output.tsv" # A unique identifier and description for each sound excerpt will be stored here. 

# Create an "audio_excerpt" directory to store the excerpted audio (if it doesn't exist already):
AUDIO_EXCERPTS = Path.cwd() / "audio_excerpts"
if not AUDIO_EXCERPTS.exists():
    AUDIO_EXCERPTS.mkdir()


# Read in the target words and strip whitespace:
with open(TARGET_WORD_LIST, "r") as file:
    lines = file.readlines()
    lines = [line.rstrip() for line in lines]

# Store the list of target words:
STRINGS = lines

# Navigate to the specified directory of wavs:
os.chdir(PATH_TO_WAVS)

## Helper function to extract audio chunk using the wave library. 

# The "source_file" argument is a path to the source wav from which the excerpt will be taken. 
# The "start_time" and "end_time" arguments indicate the timestamps delimiting the audio to be extracted. 
# The "dest_file" argument is the filename where the extracted audio will be saved.
def extract_audio(source_file, start_time, end_time, dest_file):
    with wave.open(str(source_file), "rb") as source_wav:    # Open the wave file in order to make the excerpt
        params = source_wav.getparams()                 # Obtain parameters to do framerate calculations
        fps = params.framerate                          # Store the frames-per-second in the fps variable
        start_frame = int(fps * start_time)             # Multiply fps by the start time to obtain the starting frame
        end_frame = int(fps * end_time)                 # Multiply fps by the end time to obtain the ending frame
        n_frames = end_frame - start_frame              # Subtract to obtain the total number of frames to include in the excerpt.
        source_wav.setpos(start_frame)                  # Set the position parameter of the source_wave object to the start frame
        chunk_data = source_wav.readframes(n_frames)    # Extract n_frames after the start position and store it in chunk_data
    with wave.open(dest_file, "wb") as dest_wav:    # Save the extracted chunk in the file passed to the function as dest_file
        dest_wav.setparams(params)
        dest_wav.writeframes(chunk_data)

## Helper function to search for target words in each csv and snip the audio if successful. 
## The reader argument takes in a reader object for the tsv to be searched.
## The wav_filename argument is the tsv's corresponding wav file. 
## The unique_id object allows each excerpted clip of audio to have its own unique id. It is returned
## so that the numbering continues to increment across function calls. 
def search_tsv(reader, wav_filename, unique_id):
    for row in reader:
        start_time, end_time, text = float(row[0])/1000, float(row[1])/1000, row[2] # Read in data from the tsv
        for word in STRINGS: ## This loop runs for every target word in the word list.
            if word in text.lower(): # If the target word is in the text of the transcript...
                # Extract audio chunk and save with unique id
                dest_wav_filename = os.path.join(AUDIO_EXCERPTS, f"chunk_{unique_id}.wav")
                try:
                    extract_audio(wav_filename, start_time-0.2, end_time+0.2, dest_wav_filename) # Calls the "extract_audio" function in order to do the actual wav snipping. The first try statement attempts to clip 20 milliseconds before and after the time stamps given in the tsv, in case the target word is at one of the boundaries. If that fails because the expanded boundaries are out of range, the original boundaries are used. 
                except:
                    extract_audio(wav_filename, start_time, end_time, dest_wav_filename) 
                # Write details to output csv
                writer.writerow([dest_wav_filename, wav_filename, word, start_time, end_time, text])
                unique_id += 1
    return(unique_id)

# Create list of tsvs to iterate over
tsvs = []
for filename in PATH_TO_WAVS.iterdir():
    if filename.suffix == ".tsv":
        tsvs.append(filename)


# Create or overwrite output tsv
with open(PATH_TO_OUTPUT_TSV, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile, delimiter='\t')
    writer.writerow(["Identifier", "Parent WAV", "Word" ,"Start Time", "End Time", "Text"]) # Make header
    unique_id = 0 # Set unique id
    for tsv_filename in tsvs: # Loop over every tsv in the list.
        wav_filename = Path(tsv_filename.stem + ".wav") # Find the corresponding wav file. 
        with open(tsv_filename, "r", encoding="utf-8") as tsvfile: # Open the tsv
            reader = csv.reader(tsvfile, delimiter='\t') # Create a reader
            next(reader)  # Skip header       
            for row in reader: # Search each row in the reader. 
                unique_id = search_tsv(reader, wav_filename, unique_id)

print(f"Processing complete!")
