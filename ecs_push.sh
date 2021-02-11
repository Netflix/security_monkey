#!/usr/bin/env bash

set -e
set -a

# Load the .env files. They should override in alphabetical order!
# These env vars are used in this script, and in the docker compose YAML.
# The actual containers will load their environments based on the YAML declarations
for env_file in *.env
do
    # This mess is required because
    #  - `source` only takes real files (in older bash)
    #  - The .env files don't have quotes because docker compose (or at least ecs's compose) doesn't allow it
    # So we add quotes to all env vars, write them to a temp file, and source the thing
    temp=$(mktemp)
    sed -E "s/^([A-Z_]+=)(.*$)/\1'\2'/g" <${env_file} >$temp
    source $temp
    rm $temp
done

if [ -z "$AWS_REGION" ]; then
    AWS_REGION='us-west-2'
fi

export ECS_BUILD_TIME=$(date +%s)

# Create the three task definitions
ecs-cli compose --file docker-compose-worker.yml  -r ${AWS_REGION} --task-role-arn ${SECURITY_MONKEY_ECS_WORKER_ROLE} --aws-profile ${AWS_PROFILE} -p security_monkey_worker create
ecs-cli compose --file docker-compose-front.yml  -r ${AWS_REGION} --task-role-arn ${SECURITY_MONKEY_ECS_FRONT_ROLE} --aws-profile ${AWS_PROFILE} -p security_monkey_fe create
ecs-cli compose --file docker-compose-scheduler.yml  -r ${AWS_REGION} --task-role-arn ${SECURITY_MONKEY_ECS_SCHEDULER_ROLE} --aws-profile ${AWS_PROFILE} -p security_monkey_scheduler create

# Build our docker images (ECS Compose doesn't build for you...)
docker build -t secmonkey .
docker build -t secmonkey-nginx -f docker/nginx/Dockerfile .

# Tag them locally
docker tag secmonkey:latest ${SECURITY_MONKEY_ECS_IMAGE}:latest
docker tag secmonkey:latest ${SECURITY_MONKEY_ECS_IMAGE}:$(git describe --tags)
docker tag secmonkey-nginx:latest ${SECURITY_MONKEY_ECS_NGINX_IMAGE}:latest
docker tag secmonkey-nginx:latest ${SECURITY_MONKEY_ECS_NGINX_IMAGE}:$(git describe --tags)

# Log into AWS ECR
$(aws --profile ${AWS_PROFILE} ecr get-login --no-include-email --region ${AWS_REGION})

# Push everything
docker push ${SECURITY_MONKEY_ECS_IMAGE}:latest
docker push ${SECURITY_MONKEY_ECS_IMAGE}:$(git describe --tags)
docker push ${SECURITY_MONKEY_ECS_NGINX_IMAGE}:latest
docker push ${SECURITY_MONKEY_ECS_NGINX_IMAGE}:$(git describe --tags)

# Give AWS a moment to settle (probably not required, but why not)
sleep 2

# Update the services to the newest task definition
aws --profile ${AWS_PROFILE} --region ${AWS_REGION}  ecs update-service --cluster ${AWS_ECS_CLUSTER} --service secmonkey_sched --force-new-deployment --task-definition security_monkey_scheduler
aws --profile ${AWS_PROFILE} --region ${AWS_REGION}  ecs update-service --cluster ${AWS_ECS_CLUSTER} --service secmonkey_fe --force-new-deployment --task-definition security_monkey_fe
aws --profile ${AWS_PROFILE} --region ${AWS_REGION}  ecs update-service --cluster ${AWS_ECS_CLUSTER} --service secmonkey_worker --force-new-deployment --task-definition security_monkey_worker
