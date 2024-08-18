import os
from dotenv import load_dotenv
from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codedeploy as codedeploy,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    aws_iam as iam,
    Stack,
)
from constructs import Construct

# Load environment variables from the .env file
load_dotenv()

class MyPipelineDockerStack(Stack):

    def __init__(self, scope: Construct, id: str, ec2_instance, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Access environment variables
        aws_account_id = os.getenv("AWS_ACCOUNT_ID")
        aws_region = os.getenv("AWS_REGION")
        ecr_uri = os.getenv("ECR_URI")
        repo_name = os.getenv("REPO_NAME")

        # Create an S3 bucket for the deployment artifacts
        artifact_bucket = s3.Bucket(self, "ArtifactBucket")

        # Define the artifacts
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        # Define the pipeline's source action to use CodeConnection
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="BitbucketSource",
            connection_arn=f"arn:aws:codeconnections:{aws_region}:{aws_account_id}:connection/2a7cac35-2ba0-4ba7-bb6f-240d9793d2e8",
            output=source_output,
            owner="restful_api_crud",
            repo="cdk_docker_app",
            branch="dev"
        )

        # Create a CodeBuild project for Docker image building
        build_project = codebuild.PipelineProject(self, "BuildProject",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            environment={
                'build_image': codebuild.LinuxBuildImage.STANDARD_5_0,
                'privileged': True,
                'environment_variables': {
                    'AWS_ACCOUNT_ID': codebuild.BuildEnvironmentVariable(value=aws_account_id),
                    'AWS_REGION': codebuild.BuildEnvironmentVariable(value=aws_region),
                    'ECR_URI': codebuild.BuildEnvironmentVariable(value=ecr_uri),
                    'REPO_NAME': codebuild.BuildEnvironmentVariable(value=repo_name)
                }
            }
        )

        # Add permissions to the CodeBuild project to access ECR
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:ListImages",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                resources=["*"]
            )
        )

        # Create a CodeDeploy application
        application = codedeploy.ServerApplication(self, "CodeDeployApplication",
            application_name="MyDockerApplication"
        )

        # Create a deployment group
        deployment_group = codedeploy.ServerDeploymentGroup(self, "DeploymentGroup",
            application=application,
            deployment_group_name="MyDockerDeploymentGroup",
            ec2_instance_tags=codedeploy.InstanceTagSet(
                {"Name": ["MyDockerInstance"]}
            ),
            deployment_config=codedeploy.ServerDeploymentConfig.ALL_AT_ONCE,
        )

        # Define the pipeline
        pipeline = codepipeline.Pipeline(self, "Pipeline",
            pipeline_name="MyDockerPipeline",
            artifact_bucket=artifact_bucket,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[source_action]
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="DockerBuild",
                            project=build_project,
                            input=source_output,
                            outputs=[build_output]
                        )
                    ]
                ),
                codepipeline.StageProps(
                    stage_name="Deploy",
                    actions=[
                        codepipeline_actions.CodeDeployServerDeployAction(
                            action_name="CodeDeploy",
                            deployment_group=deployment_group,
                            input=build_output
                        )
                    ]
                )
            ]
        )

        # Grant necessary permissions
        artifact_bucket.grant_read_write(pipeline.role)
