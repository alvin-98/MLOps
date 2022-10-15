"""
Module that contains the command line app.
"""
import argparse
# Imports the Google Cloud client library
import os
from google.cloud import storage

from transformers import pipeline

gcp_project = "ai5-project"
bucket_name = "ai5-mega-pipeline-bucket"
text_prompts = "text_prompts"
text_paragraphs = "text_paragraphs"


def download():

    global bucket_name, text_prompts

    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json')

    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=text_prompts+"/a")

    if not os.path.exists(text_prompts):
        os.makedirs(text_prompts)

    for blob in blobs:
        print(blob.name)
        blob.download_to_filename(blob.name)
    print("downloaded")


def generate():

    global bucket_name, text_prompts, text_paragraphs

    if not os.path.exists(text_paragraphs):
        os.makedirs(text_paragraphs)

    files = os.listdir(text_prompts)
    generator = pipeline('text-generation', model='gpt2')

    for text_file in files:

        content = open(os.path.join(text_prompts, text_file), "r")
        generated_text = generator(
            content.readline().strip(),
            max_length=100,
            num_return_sequences=1
        )

        print(generated_text[0]['generated_text'])

        with open(os.path.join(text_paragraphs, text_file), "w+") as file:
            file.write(generated_text[0]['generated_text'])

    print("generated")


def upload():
    global bucket_name, text_paragraphs
    storage_client = storage.Client.from_service_account_json(
        'secrets/mega-pipeline.json')

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(text_paragraphs)

    files = os.listdir(text_paragraphs)
    for text_file in files:
        blob.upload_from_filename(os.path.join(text_paragraphs, text_file))
    print("uploaded")


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.generate:
        generate()
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Generate text from prompt')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download text prompts from GCS bucket")

    parser.add_argument("-g", "--generate", action='store_true',
                        help="Generate a text paragraph")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload paragraph text to GCS bucket")

    args = parser.parse_args()

    main(args)
