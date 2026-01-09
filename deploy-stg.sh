#!/bin/bash
# Deploy BH Service to AWS Elastic Beanstalk - Staging Environment

set -e

# Configuration
ENVIRONMENT="stg"
APP_NAME="bh-service"
ENV_NAME="bh-service-stg"
REGION="us-east-1"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-YOUR_AWS_ACCOUNT_ID}"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}BH Service Deployment - ${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo -e "${RED}Error: EB CLI is not installed${NC}"
    echo -e "${YELLOW}Install with: pip install awsebcli${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Get version from git or timestamp
VERSION=$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d-%H%M%S)
IMAGE_TAG="${VERSION}"

echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${APP_NAME}:${IMAGE_TAG} .
docker tag ${APP_NAME}:${IMAGE_TAG} ${APP_NAME}:latest

echo -e "${YELLOW}Logging into ECR...${NC}"
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

echo -e "${YELLOW}Tagging image for ECR...${NC}"
docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}
docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REPO}:latest

echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${ECR_REPO}:${IMAGE_TAG}
docker push ${ECR_REPO}:latest

echo -e "${YELLOW}Updating Dockerrun.aws.json...${NC}"
sed -i.bak "s|<AWS_ACCOUNT_ID>|${AWS_ACCOUNT_ID}|g" Dockerrun.aws.json
sed -i.bak "s|:latest|:${IMAGE_TAG}|g" Dockerrun.aws.json

echo -e "${YELLOW}Deploying to Elastic Beanstalk...${NC}"
eb deploy ${ENV_NAME} --staged

echo -e "${YELLOW}Restoring Dockerrun.aws.json...${NC}"
mv Dockerrun.aws.json.bak Dockerrun.aws.json

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Version: ${IMAGE_TAG}${NC}"
echo -e "${YELLOW}Environment: ${ENV_NAME}${NC}"
echo ""
echo -e "${YELLOW}Check status with:${NC}"
echo -e "  eb status ${ENV_NAME}"
echo ""
echo -e "${YELLOW}View logs with:${NC}"
echo -e "  eb logs ${ENV_NAME}"
echo ""
echo -e "${YELLOW}Open in browser:${NC}"
echo -e "  eb open ${ENV_NAME}"

