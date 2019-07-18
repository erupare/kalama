from aws_cdk import (
    core,
    aws_s3,
    aws_lambda,
    aws_s3_notifications,
)

class KalamaStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs) 

        # The S3 bucket I'll drop new or updated PNG images into. This is where 
        # the image handling workflow starts
        imageBucket = aws_s3.Bucket(self, "imageBucket")

        # A lambda function to collect some info about the image, name, 
        # extension, etc
        getImageInfoFunc = aws_lambda.Function(self, "getImageInfoFunc", 
            code = aws_lambda.AssetCode('functions/getImageInfoFunc'),
            handler = "lambda.handler",
            runtime = aws_lambda.Runtime.PYTHON_3_6
        )

        # The trigger that will cause the Lambda function to be called when a 
        # PNG file is put (or copied) into the bucket
        imageBucket.add_object_created_notification(
            aws_s3_notifications.LambdaDestination(getImageInfoFunc), 
            aws_s3.NotificationKeyFilter(suffix='.png')
        )
