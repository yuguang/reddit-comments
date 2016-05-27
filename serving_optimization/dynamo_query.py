from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

table = dynamodb.Table('ngrams')

response = table.query(
    KeyConditionExpression=Key('phrase').eq('first place')
)

for i in response['Items']:
    print(i['phrase'], ":", i['date'], ":", i['percentage'])