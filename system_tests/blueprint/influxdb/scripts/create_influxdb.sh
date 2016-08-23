#!/bin/bash -e
. $(ctx download-resource "utils")

sudo apt-get update
create_opt_dir influxdb
cd /opt/influxdb

influxdb_file=$(download_component influxdb https://s3.amazonaws.com/influxdb/influxdb_0.10.1-1_amd64.deb /opt/influxdb)

install_component influxdb ${influxdb_file}
