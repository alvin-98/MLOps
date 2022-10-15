"""
Module that contains the command line app.
"""
import argparse
# Imports the Google Cloud client library
import os
from google.cloud import storage

from google.cloud import texttospeech

gcp_project = "ai5-project"
bucket_name = "ai5-mega-pipeline-bucket"
text_paragraphs = "text_paragraphs"
text_audios = "text_audios"


def download():

    global bucket_name, text_paragraphs

    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json')

    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=text_paragraphs+"/i")

    if not os.path.exists(text_paragraphs):
        os.makedirs(text_paragraphs)

    for blob in blobs:
        print(blob.name)
        blob.download_to_filename(blob.name)
    print("downloaded")


def synthesis():

    global bucket_name, text_audios, text_paragraphs

    client = texttospeech.TextToSpeechClient()

    if not os.path.exists(text_audios):
        os.makedirs(text_audios)

    files = os.listdir(text_paragraphs)

    for text_file in files:

        name = text_file.split(".")[0]

        text = ' '.join(
            open(os.path.join(text_paragraphs, text_file), 'r').readlines()
        )

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        language_code = "en-US"
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save the audio file
        audio_file = os.path.join(text_audios, name+".mp3")
        with open(audio_file, "wb") as out:
            # Write the response to the output file.
            out.write(response.audio_content)

    print("synthesized")


def upload():
    global bucket_name, text_audios

    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json'
    )

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(text_audios)

    files = os.listdir(text_audios)
    for audio_file in files:
        blob.upload_from_filename(os.path.join(text_audios, audio_file))
    print("uploaded")


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.synthesis:
        synthesis()
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Synthesis audio from text')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download paragraph of text from GCS bucket")

    parser.add_argument("-s", "--synthesis", action='store_true',
                        help="Synthesis audio")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload audio file to GCS bucket")

    args = parser.parse_args()

    main(args)
