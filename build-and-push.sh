#!/bin/bash
set -e

# Configuration
REGION="us-west-2"
PROFILE="${AWS_PROFILE:-asu-frog-sandbox}"
REPO_NAME="tabpfn-fraud-detection"
IMAGE_TAG="latest"

echo "🔍 Getting AWS account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile ${PROFILE})
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

echo "📦 Building Docker image..."
cd src/sagemaker
docker build -t ${REPO_NAME}:${IMAGE_TAG} -f Dockerfile .

echo "🏗️  Creating ECR repository (if not exists)..."
aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${REGION} --profile ${PROFILE} 2>/dev/null || \
aws ecr create-repository --repository-name ${REPO_NAME} --region ${REGION} --profile ${PROFILE}

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${REGION} --profile ${PROFILE} | \
docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

echo "🚀 Pushing image to ECR..."
docker tag ${REPO_NAME}:${IMAGE_TAG} ${IMAGE_URI}
docker push ${IMAGE_URI}

echo ""
echo "✅ Image pushed successfully!"
echo "📝 Image URI: ${IMAGE_URI}"
echo ""
echo "Add this to your .env file:"
echo "DOCKER_IMAGE_URI=${IMAGE_URI}"
