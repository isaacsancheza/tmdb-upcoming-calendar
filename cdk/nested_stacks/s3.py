import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct


class S3NestedStack(cdk.NestedStack):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str, 
            /,
            *, 
            calendars_bucket_name: str, 
            **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self, 
            'Bucket', 
            removal_policy=cdk.RemovalPolicy.DESTROY, 
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    prefix='movies',
                    enabled=True,
                    expiration=cdk.Duration.days(750),
                ),
                s3.LifecycleRule(
                    prefix='series',
                    enabled=True,
                    expiration=cdk.Duration.days(750),
                ),
            ],
        )

        self.calendars_bucket = s3.Bucket.from_bucket_name(
            self, 
            'CalendarsBucket', 
            bucket_name=calendars_bucket_name,
        )
