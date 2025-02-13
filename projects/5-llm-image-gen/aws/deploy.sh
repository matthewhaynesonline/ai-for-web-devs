#!/usr/bin/env bash

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source $script_dir/aws.env

project_dir_path="$server_home_dir/$project_dir_name"

# dry_run=true
dry_run=false

if [ "$dry_run" = true ]; then
  echo
  echo "Checking code diff"
  echo
  rsync -avn --itemize-changes -P --include="docker-compose.yml" --include=".env" --include="app/***" --exclude="*" $script_dir/../ $ssh_connection:$project_dir_path
else
  echo
  echo "Deploying code"
  echo
  rsync -a -P --include="docker-compose.yml" --include=".env" --include="app/***" --exclude="*" $script_dir/../ $ssh_connection:$project_dir_path
fi


# echo
# echo "Starting Docker Stack"
# echo
# ssh $ssh_connection <<EOF
#   cd $project_dir_path
#   docker compose stop; docker compose up --build -d
# EOF
