#!/bin/bash -e
. $(ctx download-resource "utils")

sudo cat >/etc/yum.repos.d/influxdb.repo << EOL
[influxdb]
name = InfluxDB Repository - RHEL \$releasever
baseurl = https://repos.influxdata.com/rhel/\$releasever/\$basearch/stable
enabled = 1
gpgcheck = 1
gpgkey = https://repos.influxdata.com/influxdb.key
EOL

sudo yum install influxdb
sudo service influxdb start


