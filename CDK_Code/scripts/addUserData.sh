#!/bin/bash

# Set strict mode for script execution
set -euo pipefail

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the relative path to the .env file
ENV_FILE_PATH="$SCRIPT_DIR/../../.env"

# Source the .env file to load environment variables
if [ -f "$ENV_FILE_PATH" ]; then
  export $(grep -v '^#' "$ENV_FILE_PATH" | xargs)
else
  echo ".env file not found at $ENV_FILE_PATH"
  exit 1
fi

# Update the system
sudo yum update -y

# Install Docker
sudo amazon-linux-extras install docker -y

# Start Docker service
sudo service docker start

# Add ec2-user to the docker group
sudo usermod -a -G docker ec2-user

# Login to ECR using environment variables
docker login -u AWS -p $(aws ecr get-login-password --region "$AWS_REGION") "$ECR_URI"

# Pull the latest Docker image from ECR
docker pull "$ECR_URI/$REPO_NAME:latest"

# Run the Docker container
docker run -d -p 80:8000 "$ECR_URI/$REPO_NAME:latest"

echo "Deployment script completed successfully."
