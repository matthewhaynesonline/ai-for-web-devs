#!/usr/bin/env bash

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source $script_dir/aws.env

project_dir_path="$server_home_dir/$project_dir_name"

echo
echo "Configuring EC2"
echo
ssh $ssh_connection <<EOF
  echo
  echo "Creating Project Directories"
  echo
  mkdir -p $project_dir_path
  mkdir -p $project_dir_path/models

  echo
  echo "Downloading LLM Model File"
  echo
  cd $project_dir_path/models
  curl -O -L $model_file_download_url

  # Test NVIDIA container
  docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
EOF
