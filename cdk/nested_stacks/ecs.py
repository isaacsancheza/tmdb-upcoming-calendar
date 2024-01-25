import aws_cdk as cdk
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_applicationautoscaling as appscaling
from aws_cdk import aws_ecs_patterns as ecs_patterns
from constructs import Construct

from nested_stacks.s3 import S3NestedStack
from nested_stacks.ssm import SSMNestedStack


class ECSNestedStack(cdk.NestedStack):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str, 
            /,
            *,
            region: str,
            account: str,
            image_repository: str,
            s3_nested_stack: S3NestedStack,
            ssm_nested_stack: SSMNestedStack,
            **kwargs,
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image = ecs.EcrImage.from_registry(image_repository)
        
        vpc = ec2.Vpc.from_lookup(
            self, 
            'Vpc', 
            region=region,
            is_default=True, 
            owner_account_id=account, 
        )
        
        cluster = ecs.Cluster(
            self, 
            'Cluster', 
            vpc=vpc,
        )
        cluster.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        scheduled_fargate_task = ecs_patterns.ScheduledFargateTask(
            self, 
            'ScheduledFargateTask', 
            cluster=cluster, 
            scheduled_fargate_task_image_options=ecs_patterns.ScheduledFargateTaskImageOptions(
                image=image, 
                cpu=256,
                memory_limit_mib=512, 
                environment={
                    'BUCKET_NAME': s3_nested_stack.bucket.bucket_name,
                    'CALENDARS_BUCKET_NAME': s3_nested_stack.calendars_bucket.bucket_name,
                    'ACCESS_TOKEN_PARAMETER_NAME': ssm_nested_stack.access_token_parameter.parameter_name,
                },
            ),
            schedule=appscaling.Schedule.rate(cdk.Duration.days(7)),
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )
        
        s3_nested_stack.bucket.grant_read_write(scheduled_fargate_task.task_definition.task_role)
        s3_nested_stack.calendars_bucket.grant_write(scheduled_fargate_task.task_definition.task_role)
        ssm_nested_stack.access_token_parameter.grant_read(scheduled_fargate_task.task_definition.task_role)
