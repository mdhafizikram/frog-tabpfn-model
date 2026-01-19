#!/bin/bash
set -e

# Configuration
REGION="us-west-2"
PROFILE="${AWS_PROFILE:-asu-frog-sandbox}"
REPO_NAME="tabpfn-fraud-detection"

echo "🗑️  Removing Docker images from ECR..."

# Check if repository exists
if aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${REGION} --profile ${PROFILE} 2>/dev/null; then
  
  # List all images
  IMAGES=$(aws ecr list-images --repository-name ${REPO_NAME} --region ${REGION} --profile ${PROFILE} --query 'imageIds[*]' --output json)
  
  if [ "$IMAGES" != "[]" ]; then
    echo "📋 Found images in repository: ${REPO_NAME}"
    
    # Delete all images
    aws ecr batch-delete-image \
      --repository-name ${REPO_NAME} \
      --region ${REGION} \
      --profile ${PROFILE} \
      --image-ids "$IMAGES" \
      --output text
    
    echo "✅ All images deleted from ${REPO_NAME}"
  else
    echo "ℹ️  No images found in repository: ${REPO_NAME}"
  fi
  
  # Optionally delete the repository itself
  read -p "Delete the ECR repository '${REPO_NAME}' as well? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    aws ecr delete-repository \
      --repository-name ${REPO_NAME} \
      --region ${REGION} \
      --profile ${PROFILE} \
      --force
    echo "✅ Repository ${REPO_NAME} deleted"
  else
    echo "ℹ️  Repository kept (empty)"
  fi
  
else
  echo "ℹ️  Repository ${REPO_NAME} does not exist"
fi

echo ""
echo "Done!"
