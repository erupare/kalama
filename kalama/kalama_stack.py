from aws_cdk import (
    core,
    aws_s3,
    aws_events,
    aws_lambda,
    aws_cloudtrail,
    aws_stepfunctions,
    aws_events_targets,
    aws_stepfunctions_tasks
)

class KalamaStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs) 

        # The start of the image pipeline
        imageBucket = aws_s3.Bucket(self, "imageBucket")
        
        # Capture API activity with a trail
        imageBucketTrail = aws_cloudtrail.Trail(self, "imageBucketTrail",
            is_multi_region_trail = False)

        # Restrict to S3 data-plane events
        imageBucketTrail.add_s3_event_selector(
            include_management_events = False,
            prefixes = [f"{imageBucket.bucket_arn}/"],
            read_write_type = aws_cloudtrail.ReadWriteType.WRITE_ONLY)

        # Filter to just PutObject and CopyObject events
        imageBucketRule = aws_events.Rule(self, "imageBucketRule", 
            event_pattern = {
                "source": ["aws.s3"],
                "detail": {
                    "eventSource": ["s3.amazonaws.com"],
                    "eventName": ["PutObject", "CopyObject"],
                    "requestParameters": { "bucketName": [imageBucket.bucket_name]}}})

        # Gather info about an image, name, extension, etc
        getImageInfoFunc = aws_lambda.Function(self, "getImageInfoFunc", 
            code = aws_lambda.AssetCode('functions/getImageInfoFunc'),
            handler = "lambda.handler",
            runtime = aws_lambda.Runtime.PYTHON_3_6)

        # Results of file extension check
        yesPng = aws_stepfunctions.Succeed(self, "Yes, a PNG")
        notPng = aws_stepfunctions.Succeed(self, "Not a PNG")

        # Verify the file extension
        checkForPng = aws_stepfunctions.Choice(self, 'Is a PNG?')
        checkForPng.when(aws_stepfunctions.Condition.string_equals('$.extension', 'png'), yesPng)
        checkForPng.otherwise(notPng);

        # A single image pipeline job for testing
        getImageInfoJob = aws_stepfunctions.Task(self, 'Get image info', 
            task = aws_stepfunctions_tasks.InvokeFunction(getImageInfoFunc))
        getImageInfoJob.next(checkForPng)

        # Configure the image pipeline and starting state
        imagePipeline = aws_stepfunctions.StateMachine(self, "imagePipeline",
            definition = getImageInfoJob)

        # Matching events start the image pipline
        imageBucketRule.add_target(
            aws_events_targets.SfnStateMachine(imagePipeline, 
                input = aws_events.RuleTargetInput.from_event_path("$.detail.requestParameters")))