import os
import re
import json
import boto3
from datetime import datetime

ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['PAGETABLE'])

def handler(event, context):

  name = event['name']
  
  title = name.split('_')[0]
  title = re.sub(r"[-]", ' ', title)
  title = re.sub(r"\s+", ' ', title)
  
  updated = datetime.fromtimestamp(event['timestamp']).isoformat()

  response = table.update_item(
      Key={ 'pageName': name },
      UpdateExpression="set pageCreated = if_not_exists (pageCreated, :pageUpdated), pageLink = if_not_exists (pageLink, :pageLink), pageUpdated = :pageUpdated, pageImage = :pageImage, pageThumbnail = :pageThumbnail, pageTitle = :pageTitle, pageStatus = if_not_exists (pageStatus, :pageStatus)",
      ExpressionAttributeValues={
          ":pageUpdated"    : updated,
          ":pageImage"      : event['images'][0], 
          ":pageThumbnail"  : event['images'][1],
          ":pageLink"       : f"{os.environ['PAGEPREFIX']}{name}/",
          ":pageTitle"      : title,
          ":pageStatus"     : 'draft'
      },
      ReturnValues="ALL_NEW"
  )    
  
  return response['Attributes']
