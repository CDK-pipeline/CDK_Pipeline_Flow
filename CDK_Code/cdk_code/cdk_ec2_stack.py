from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    Stack,
    Tags,
)
from constructs import Construct
import os

class MyEC2DockerStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define a VPC
        vpc = ec2.Vpc(self, "MyVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Define an IAM role for the instance
        role = iam.Role(self, "InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforAWSCodeDeploy")
            ]
        )

        # Define a security group
        security_group = ec2.SecurityGroup(self, "InstanceSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for EC2 instance"
        )

        # Add inbound rule for SSH and HTTP
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="Allow SSH access"
        )

        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP access"
        )

        # Define the EC2 instance and assign it to self.instance
        self.instance = ec2.Instance(self, "MyDockerInstance",
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            role=role,
            security_group=security_group,
            key_name="my-ec2-keypair"  # Make sure this key pair exists in your AWS account
        )

        # Read the user data script
        user_data_script = open('scripts/addUserData.sh').read()

        # Add user data script to the instance
        self.instance.add_user_data(user_data_script)

        # Tag the instance
        Tags.of(self.instance).add("Name", "MyDockerInstance")
