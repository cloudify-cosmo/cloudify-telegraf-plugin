#!/bin/bash

set -e

sudo service docker start
sudo docker run ubuntu
sudo docker run hello-world
