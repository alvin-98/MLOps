"""
Module that contains the command line app.
"""
import argparse
from tempfile import TemporaryDirectory
# Imports the Google Cloud client library
from google.cloud import speech
import os
import ffmpeg
import io
from google.cloud import storage

gcp_project = "ai5-project"
bucket_name = "ai5-mega-pipeline-bucket"
input_audios = "input_audios"
text_prompts = "text_prompts"


def download():

    global bucket_name, input_audios

    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json')

    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=input_audios)

    if not os.path.exists(input_audios):
        os.makedirs(input_audios)

    for blob in blobs:
        print(blob.name)
        blob.download_to_filename(blob.name)
    print("downloaded")


def transcribe():

    # Instantiates a client
    client = speech.SpeechClient()

    global bucket_name, input_audios, text_prompts

    flac_files = 'flac_files'
    if not os.path.exists(text_prompts):
        os.makedirs(text_prompts)
    if not os.path.exists(flac_files):
        os.makedirs(flac_files)

    audio_files = os.listdir(input_audios)
    for audio_file in audio_files:
        audio_name = audio_file.split(".")[0]

        flac_path = os.path.join(flac_files, audio_name+".flac")
        audio_path = os.path.join(input_audios, audio_file)
        stream = ffmpeg.input(audio_path)
        stream = ffmpeg.output(stream, flac_path)
        ffmpeg.run(stream)

        with io.open(flac_path, "rb") as audio_file:
            content = audio_file.read()

        # Transcribe
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            language_code="en-US"
        )

        operation = client.long_running_recognize(
            config=config, audio=audio)
        response = operation.result(timeout=90)

        print(response)

        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))
            transcript = result.alternatives[0].transcript

            # store in text files
            txt_name = audio_name+".txt"
            with open(os.path.join(text_prompts, txt_name), "w+") as txt_file:
                txt_file.write(transcript)

    print("transcribed")


def upload():
    global bucket_name, text_prompts
    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json')

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(text_prompts)

    files = os.listdir(text_prompts)
    for text_file in files:
        blob.upload_from_filename(os.path.join(text_prompts, text_file))
    print("uploaded")


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.transcribe:
        transcribe()
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Transcribe audio file to text')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download audio files from GCS bucket")

    parser.add_argument("-t", "--transcribe", action='store_true',
                        help="Transcribe audio files to text")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload transcribed text to GCS bucket")

    args = parser.parse_args()

    main(args)
