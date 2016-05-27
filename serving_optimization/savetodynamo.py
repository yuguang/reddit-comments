from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
import argparse, csv


parser = argparse.ArgumentParser()
parser.add_argument("file", help="A CSV file without header, one datum per line")
args = parser.parse_args()
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

table = dynamodb.Table('Ngram')

with open(args.file, 'rb') as file:
    reader = csv.reader(file)
    for line in reader:
        if not ''.join(line).strip():
            continue
        if len(line) != 6:
            continue
        date, name, count, total, length, percentage = line
        print("Adding ngram:", date, name)

        table.put_item(
           Item={
               'Date': date,
               'Phrase': name,
               'Percentage': percentage,
            }
        )