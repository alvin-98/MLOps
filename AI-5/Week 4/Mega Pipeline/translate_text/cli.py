"""
Module that contains the command line app.
"""
import argparse
# Imports the Google Cloud client library
import os
from google.cloud import storage

from googletrans import Translator

gcp_project = "ai5-project"
bucket_name = "ai5-mega-pipeline-bucket"
text_paragraphs = "text_paragraphs"
text_translated = "text_translated"


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


def translate():

    global bucket_name, text_translated, text_paragraphs

    if not os.path.exists(text_translated):
        os.makedirs(text_translated)

    files = os.listdir(text_paragraphs)

    for text_file in files:

        text = ' '.join(
            open(os.path.join(text_paragraphs, text_file), 'r').readlines()
        )

        translator = Translator()
        results = translator.translate(text, src="en", dest="hi")

        # store in text files
        with open(os.path.join(text_translated, text_file), "w+") as file:
            file.write(results.text)

    print("translated")


def upload():
    global bucket_name, text_translated

    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json'
    )

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(text_translated)

    files = os.listdir(text_translated)
    for text_file in files:
        blob.upload_from_filename(os.path.join(text_translated, text_file))
    print("uploaded")


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.translate:
        translate()
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Translate English to Hindi')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download text paragraphs from GCS bucket")

    parser.add_argument("-t", "--translate", action='store_true',
                        help="Translate text")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload translated text to GCS bucket")

    args = parser.parse_args()

    main(args)
