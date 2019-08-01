import os
import datetime

def handler(event, context):

    # Grab the interesting bits from the event
    key = event['key']

    head, tail = os.path.split(key)  
    name, extension = tail.rsplit('.',2)

    return { 
        'name': name,
        'extension': extension, 
        'timestamp': int(datetime.datetime.utcnow().timestamp()), 
        'source': {'bucket': event['bucketName'], 'key': key}}