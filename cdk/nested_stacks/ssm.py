import aws_cdk as cdk
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class SSMNestedStack(cdk.NestedStack):
    def __init__(
            self, 
            scope: Construct, 
            construct_id: str,
            /,
            access_token_parameter_name: str, 
            **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.access_token_parameter = ssm.StringParameter.from_secure_string_parameter_attributes(
            self, 
            'AccessTokenParameter', 
            parameter_name=access_token_parameter_name
        )
