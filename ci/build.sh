#!/bin/bash

set -eu

SM_CONTAINER="secmonkey"
SM_TAG="latest"
SM_IMAGE="$SM_CONTAINER:$SM_TAG"
UPSTREAM_REMOTE="https://github.com/Netflix/security_monkey.git"

function cleanup_db
{
    echo "Cleaning DB container" 1>&2
    docker rm -f $DB_NAME &>/dev/null
    exit $1
}

case "$1" in
    build_dart)
        docker build -t "$SM_IMAGE" ./ci/
        docker run --rm -v "$PWD":/usr/src/app "$SM_IMAGE" /usr/src/app/ci/build_dart.sh
        ;;
    unit)
        PSQL_ID=$(docker run -d postgres:9.2)
        # Sleep to ensure pgsql container is ready
        sleep 3
        # Get name of DB container
        DB_NAME=$(docker ps -a --format "{{.Names}}" --filter "id=$PSQL_ID")
        docker build -t "$SM_IMAGE" ./ci/
        docker run --rm --link $DB_NAME:db -v "$PWD":/usr/src/app "$SM_IMAGE" || cleanup_db 1
        cleanup_db 0
        ;;
    lint)
        echo "Fetching upstream changes"
        [[ $(git remote | grep netflix) ]] || git remote add netflix "$UPSTREAM_REMOTE"
        git fetch netflix
        echo "Finding BW-added py files"
        bw_added=$(git diff --name-only --diff-filter=A netflix/master -- security_monkey | grep .py)
        echo "Finding current changes in bw-added py files only"
        changed=$(git diff-tree --no-commit-id --name-only -r HEAD --relative -- $bw_added)
        [[ $changed ]] || { echo "No changes detected in bw-added py files"; exit 0; }
        docker build -t "$SM_IMAGE" ./ci/
        echo "Checking style for $changed"
        docker run --rm -v "$PWD":/usr/src/app "$SM_IMAGE" /usr/src/venv/bin/flake8 $changed
        ;;
    *)
        echo "Invalid build type: $1"
        exit 1
esac
