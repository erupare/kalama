import os
import cv2
import boto3
import numpy

s3 = boto3.client('s3')

THUMBNAIL_WIDTH = 640
THUMBNAIL_HEIGHT = 480

def handler(event, context):
  
  object = s3.get_object(Bucket=event['source']['bucket'], Key=event['source']['key'])
  content = object["Body"].read() 
  
  image = numpy.asarray(bytearray(content), dtype="uint8")
  image = cv2.imdecode(image,1)

  newsize = (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
  image = cv2.resize(image, newsize)
  image = cv2.imencode(".png", image)[1].tostring()  
  
  key = f"{os.environ['OUTPUTPREFIX']}{event['name']}-{event['timestamp']}-sm.{event['extension']}"
  
  response = s3.put_object(
      Bucket = os.environ['OUTPUTBUCKET'], 
      Key = key, 
      Body = image, 
      ContentType = 'image/png', 
      ACL = 'public-read', 
      CacheControl = "max-age=31536000")

  return key