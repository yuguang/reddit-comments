from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
import argparse, csv


parser = argparse.ArgumentParser()
parser.add_argument("file", help="A CSV file without header, one datum per line")
args = parser.parse_args()
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

table = dynamodb.Table('ngrams')

with open(args.file, 'rb') as file:
    reader = csv.reader(file)
    for line in reader:
        if not ''.join(line).strip():
            continue
        if len(line) != 6:
            continue
        date, name, count, total, length, percentage = line
        # remove the century part of the year and dashes
        date = date.replace('-', '')[2:]
        # truncate to significant digits
        percentage_trunc = int(round(float(percentage)*pow(10, 8)))
        print("Adding ngram:", date, name, percentage_trunc)

        table.put_item(
           Item={
               'date': date,
               'phrase': name,
               'percentage': percentage_trunc,
            }
        )