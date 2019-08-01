import os
import json
import boto3

s3 = boto3.client('s3')

def handler(event, context):
  
    object = s3.get_object(Bucket=event['source']['bucket'], Key=event['source']['key'])
    content = object["Body"].read() 
  
    key = f"{os.environ['OUTPUTPREFIX']}{event['name']}-{event['timestamp']}.{event['extension']}"
    response = s3.put_object(
        Bucket=os.environ['OUTPUTBUCKET'], 
        Key=key, 
        Body=content, 
        ContentType='image/png', 
        ACL='public-read', 
        CacheControl= "max-age=31536000") # 1 year

    return key
