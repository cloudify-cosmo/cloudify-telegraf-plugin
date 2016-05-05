#!/bin/bash

set -e

sudo service docker start
sudo docker run hello-world bin/sleep 1800
