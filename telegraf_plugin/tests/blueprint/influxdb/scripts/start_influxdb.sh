#!/bin/bash -e
. $(ctx download-resource "utils")

start_service influxdb

sleep 10 #waiting for influxdb server to start

ctx logger info "InfluxDB server is up, creating database name 'monitoring_telegraf'..."
influx -host $(ctx instance host_ip) -execute="CREATE DATABASE monitoring_telegraf"

