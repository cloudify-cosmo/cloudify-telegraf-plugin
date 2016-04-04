#!/bin/bash -e
. $(ctx download-resource "components/utils")

start_service influxdb

sleep 10 #waiting for influxdb server to start

if [ $(ctx node id) = 'influxdb_master' ]; then
	ctx logger info "InfluxDB server is up, creating database name 'db1'..."
	influx -host $(ctx instance host_ip) -execute="CREATE DATABASE db1"
fi
