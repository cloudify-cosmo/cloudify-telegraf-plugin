#!/bin/bash

set -e

sudo service docker start
sudo docker run ubuntu /bin/sleep 600
