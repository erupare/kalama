from aws_cdk import (
    core,
    aws_s3,
    aws_events,
    aws_lambda,
    aws_dynamodb,
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

        #--
        #  Lambda Layers 
        #--------------------#

        opencvLayer = aws_lambda.LayerVersion(self, 'opencvLayer',
            code = aws_lambda.AssetCode('layers/opencvLayer'),
            compatible_runtimes = [aws_lambda.Runtime.PYTHON_3_6])

        boto3Layer = aws_lambda.LayerVersion(self, 'boto3Layer',
            code = aws_lambda.AssetCode('layers/boto3Layer'),
            compatible_runtimes = [aws_lambda.Runtime.PYTHON_3_6])

        #--
        #  Lambda Functions
        #--------------------#

        # Gather info about an image, name, extension, etc
        getImageInfoFunc = aws_lambda.Function(self, "getImageInfoFunc", 
            code = aws_lambda.AssetCode('functions/getImageInfoFunc'),
            handler = "lambda.handler",
            runtime = aws_lambda.Runtime.PYTHON_3_6)

        # The home for the website
        webBucket = aws_s3.Bucket(self, "webBucket", 
            website_index_document = 'index.html')
            
        # Copy the image to the web bucket
        copyImageFunc = aws_lambda.Function(self, "copyImageFunc",
            code = aws_lambda.AssetCode('functions/copyImageFunc'),
            handler = "lambda.handler",
            runtime = aws_lambda.Runtime.PYTHON_3_6,
            layers = [boto3Layer], 
            environment = {
                'OUTPUTBUCKET': webBucket.bucket_name, 
                'OUTPUTPREFIX': 'images/'})
                
        # Grant permissions to read from the source and write to the desination        
        imageBucket.grant_read(copyImageFunc)
        webBucket.grant_write(copyImageFunc)

        # Create a thumbnail of the image and place in the web bucket
        createThumbnailFunc = aws_lambda.Function(self, "createThumbnailFunc",
            code = aws_lambda.AssetCode('functions/createThumbnailFunc'),
            handler = "lambda.handler",
            runtime = aws_lambda.Runtime.PYTHON_3_6,
            layers = [boto3Layer, opencvLayer], 
            timeout = core.Duration.seconds(10),
            memory_size = 256, 
            environment = {
                'OUTPUTBUCKET': webBucket.bucket_name, 
                'OUTPUTPREFIX': 'images/'})
                
        # Grant permissions to read from the source and write to the desination        
        imageBucket.grant_read(createThumbnailFunc)
        webBucket.grant_write(createThumbnailFunc)

        # Store page information
        pageTable = aws_dynamodb.Table(self, 'pageTable',
          partition_key = { 'name': 'pageName', 'type': aws_dynamodb.AttributeType.STRING },
          billing_mode = aws_dynamodb.BillingMode.PAY_PER_REQUEST,
          stream = aws_dynamodb.StreamViewType.NEW_IMAGE)

        # Save page and image information
        updatePageInfoFunc = aws_lambda.Function(self, "updatePageInfoFunc",
            code = aws_lambda.AssetCode('functions/updatePageInfoFunc'),
            handler = "lambda.handler",
            runtime = aws_lambda.Runtime.PYTHON_3_6,
            layers = [boto3Layer], 
            environment = {
                'PAGETABLE': pageTable.table_name,
                'PAGEPREFIX': 'posts/'
            }
        )
        
        # Grant permissions to write to the page table
        pageTable.grant_write_data(updatePageInfoFunc)            

        imagePipelineDone = aws_stepfunctions.Succeed(self, "Done processing image")

        updatePageInfoJob = aws_stepfunctions.Task(self, 'Update page info', 
            task = aws_stepfunctions_tasks.InvokeFunction(updatePageInfoFunc))
        updatePageInfoJob.next(imagePipelineDone)

        copyImageJob = aws_stepfunctions.Task(self, 'Copy image', 
            task = aws_stepfunctions_tasks.InvokeFunction(copyImageFunc))

        createThumbnailJob = aws_stepfunctions.Task(self, 'Create thumbnail', 
            task = aws_stepfunctions_tasks.InvokeFunction(createThumbnailFunc))

        # These tasks can be done in parallel
        processImage = aws_stepfunctions.Parallel(self, 'Process image',
            result_path = "$.images")

        processImage.branch(copyImageJob)
        processImage.branch(createThumbnailJob)
        processImage.next(updatePageInfoJob)

        # Results of file extension check
        notPng = aws_stepfunctions.Succeed(self, "Not a PNG")

        # Verify the file extension
        checkForPng = aws_stepfunctions.Choice(self, 'Is a PNG?')
        checkForPng.when(aws_stepfunctions.Condition.string_equals('$.extension', 'png'), processImage)
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