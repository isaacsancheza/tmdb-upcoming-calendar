from os import environ

import aws_cdk as cdk

from stack import Stack


region = environ['REGION']
account = environ['ACCOUNT']
stack_name = environ['STACK_NAME']
image_repository = environ['IMAGE_REPOSITORY']
calendars_bucket_name = environ['CALENDARS_BUCKET_NAME']
access_token_parameter_name = environ['ACCESS_TOKEN_PARAMETER_NAME']

app = cdk.App()
env = cdk.Environment(region=region, account=account)

Stack(
    app, 
    'Stack', 
    env=env, 
    region=region,
    account=account,
    stack_name=stack_name,
    image_repository=image_repository,
    calendars_bucket_name=calendars_bucket_name,
    access_token_parameter_name=access_token_parameter_name,
)

cdk.Tags.of(app).add('stack-name', stack_name)
app.synth()
