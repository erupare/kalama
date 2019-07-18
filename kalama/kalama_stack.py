from aws_cdk import (
    core,
    aws_s3,
    aws_cloudtrail,
)

class KalamaStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs) 

        # The start of the image pipeline
        imageBucket = aws_s3.Bucket(self, "imageBucket")
        
        # Capture API activity with a trail
        imageBucketTrail = aws_cloudtrail.Trail(self, "imageBucketTrail",
            is_multi_region_trail = False)

        # Restrict to image bucket data-plane events
        imageBucketTrail.add_s3_event_selector(
            include_management_events = False,
            prefixes = [f"{imageBucket.bucket_arn}/"],
            read_write_type = aws_cloudtrail.ReadWriteType.WRITE_ONLY)
