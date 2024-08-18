#!/usr/bin/env python3
import os
import aws_cdk as cdk

from cdk_code.cdk_pipeline_stack import MyPipelineDockerStack
from cdk_code.cdk_ec2_stack import MyEC2DockerStack

# Load environment variables
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
AWS_REGION = os.getenv('AWS_REGION')

app = cdk.App()

# Create the EC2 stack
ec2_stack = MyEC2DockerStack(app, "MyEC2DockerStack", env={
    'account': AWS_ACCOUNT_ID, 'region': AWS_REGION
})

# Create the Pipeline stack and pass the ec2_instance from the EC2 stack
MyPipelineDockerStack(app, "MyPipelineDockerStack", ec2_instance=ec2_stack.instance, env={
    'account': AWS_ACCOUNT_ID, 'region': AWS_REGION
})

app.synth()
