import json

def handler(event, context):

  for record in event['Records']:
    
    file = {
      'bucket': record['s3']['bucket']['name'],
      'key': record['s3']['object']['key'],
    }
    
    print(json.dumps(file))        