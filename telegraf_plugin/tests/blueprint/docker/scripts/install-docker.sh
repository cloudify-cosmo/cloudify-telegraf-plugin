#!/bin/bash

set -e

sudo yum update
sudo tee /etc/yum.repos.d/docker.repo <<-'EOF'

sudo yum install docker-engine
sudo service docker start
sudo docker run hello-world
