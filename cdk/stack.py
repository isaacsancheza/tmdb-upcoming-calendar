import aws_cdk as cdk
from constructs import Construct

from nested_stacks.s3 import S3NestedStack
from nested_stacks.ecs import ECSNestedStack
from nested_stacks.ssm import SSMNestedStack


class Stack(cdk.Stack):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str, 
            /,
            *, 
            region: str,
            account: str,
            image_repository: str,
            calendars_bucket_name: str, 
            access_token_parameter_name: str,
            **kwargs
        ):
        super().__init__(scope, construct_id, **kwargs)

        s3_nested_stack = S3NestedStack(
            self, 
            'S3NestedStack',
            calendars_bucket_name=calendars_bucket_name,
        )
        ssm_nested_stack = SSMNestedStack(
            self,
            'SSMNestedStack',
            access_token_parameter_name=access_token_parameter_name
        )
        ecs_nested_stack = ECSNestedStack(
            self,
            'ECSNestedStack',
            region=region,
            account=account,
            image_repository=image_repository,
            s3_nested_stack=s3_nested_stack,
            ssm_nested_stack=ssm_nested_stack,
        )

        cdk.CfnOutput(
            self,
            'BucketName',
            value=s3_nested_stack.bucket.bucket_name,
        )
