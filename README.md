**WIP**

cloudify-telegraf-plugin
========================

* Master Branch [![CircleCI](https://circleci.com/gh/cloudify-cosmo/cloudify-telegraf-plugin.svg?style=svg)](https://circleci.com/gh/cloudify-cosmo/cloudify-telegraf-plugin)

## Description

cloudify-telegraf-plugin is used to install & configure [Telegraf](https://influxdata.com/time-series-platform/telegraf/) monitoring platrofm on hosts.
Telgraf plaforms allows to collect time-series data from variety of sources ([inputs](https://docs.influxdata.com/telegraf/v0.13/inputs/)) and send them to desired destination ([outputs](https://docs.influxdata.com/telegraf/v0.13/outputs/)).

## Usage
cloudify-telegraf-plugin usage is very simple and require no more than config parameters as inputs. 
for each node which required telegraf platform - just enable the "monitoring agent" under the 'interface' section and provide the desired inputs. for example:

```yaml
VM:
    type: cloudify.openstack.nodes.Server
    properties:
      resource_id:
      cloudify_agent:
    interfaces:
      cloudify.interfaces.monitoring_agent:
        install:
          implementation: telegraf.telegraf_plugin.tasks.install
          inputs:
            telegraf_install_path: /opt/telegraf
            download_url:
            telegraf_config_file:
            telegraf_config_inputs:
              outputs:
                influxdb:
                  urls:
                    - http://localhost:8086
                  database: monitoring_telegraf
              inputs:
                mem:
                system:
                cpu:
                  percpu: false
                  totalcpu: true
                  drop:
                    - cpu_time
                disk:
        start:
            implementation: telegraf.telegraf_plugin.tasks.start
```
As you can see, in order to add telegraf platform to node - we provided 'telegraf_config_inputs' which is a dict with the following mandatory sub-dicts:
* **inputs**
* **outputs**

during the plugin installation process, a valid config file is generated - base on the inputs which provided.

Another option is to provide a ready and valid configuration file under 'telegraf_config_file' input (by default, this input is None).

> Notice! in order to provide valid inputs\config file, follow the [configuration editting instructions.](https://docs.influxdata.com/telegraf/v0.13/introduction/getting_started/#configuration)

Two additional inputs are:
* **telegraf_install_path** - sets the directory which thw system will be downloaded and install in (by default - set to be: /opt/telegraf)
* **download_url** - sets the url which telegraf will be downloaded from (by defaults - set to be from http://get.influxdb.org/telegraf, version 0.12.0)



