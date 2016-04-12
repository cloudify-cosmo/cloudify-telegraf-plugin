########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
########

# ctx is imported and used in operations
from cloudify import ctx
from cloudify import exceptions

# put the operation decorator on any function that is a task
from cloudify.decorators import operation
import os
from sys import platform as _platform
import ld
from subprocess import call, Popen


@operation
def install(**kwargs):
    # running the full flow of generating telegraf service.
    ctx.logger.info("Installing telegraf...")
    create()
    ctx.logger.info("Telegraf service was installed...")
    ctx.logger.info("configuring telegraf.toml...")
    configure()
    ctx.logger.info("telegraf.conf was configured...")


@operation
def create(telegraf_path=None, download_url=None, **kwargs):
    # download and install the telegraf servivce
    if telegraf_path is None:
        telegraf_path = '/opt/telegraf'

    ctx.instance.runtime_properties['telegraf_path'] = telegraf_path

    if not os.path.exists(telegraf_path):
        cmd = 'sudo mkdir -p {0}'.format(telegraf_path)
        call(cmd.split())

    os.chdir(telegraf_path)

    if _platform == "linux" or _platform == "linux2":
        dist = ld.linux_distribution(full_distribution_name=False)[0]
        if dist == 'ubuntu' or dist == 'debian':
            if download_url is None:
                download_url = 'http://get.influxdb.org/telegraf/telegraf_0.12.0-1_amd64.deb'
            ctx.logger.info('downloading telegraf...')
            Popen('sudo wget {0}'.format(download_url), shell=True)
            ctx.logger.info('telegraf downloaded...installing..')
            telegraf_file = download_url.rsplit('/', 1)[-1]
            cmd = 'sudo dpkg -i {0}'.format(telegraf_file)
            return_code = call(cmd, shell=True)
            if return_code != 0:
                raise exceptions.NonRecoverableError(
                    'Unable to install Telegraf service')
        elif dist == 'centos' or dist == 'redhat':
            if download_url is None:
                download_url = 'sudo wget http://get.influxdb.org/telegraf/telegraf-0.12.0-1.x86_64.rpm'
            Popen('sudo wget {0}'.format(download_url))
            ctx.logger.info('telegraf downloaded...installing..')
            Popen('sudo yum localinstall {0}'.format(
                download_url.rsplit('/', 1)[-1]))


@operation
def configure(**kwargs):
    # generating configuration file with elected outputs & inputs.
    # input is dict\json
    conf_file = ctx.download_resource_and_render('telegraf.conf')
    cmd = 'sudo mv {0} /etc/telegraf/telegraf.conf'.format(conf_file)
    Popen(cmd, shell=True)


@operation
def start(config_file=None, **kwargs):
    # starting the telegraf service with the right config file
    # need to validate inputs\outputs correctness?
    ctx.logger.info("starting telegraf service...")
    if config_file is None:
        config_file = '/etc/telegraf/telegraf.conf'
    if not os.path.isfile(config_file):
        raise exceptions.NonRecoverableError("Config file doesn't exists")

    cmd = 'sudo service telegraf start'
    return_code = call(cmd, shell=True)
    if return_code != 0:
        raise exceptions.NonRecoverableError(
            'Telegraf service failed to start')
    ctx.logger.info("GoodLuck! telegraf service is up!\
                    have an awesome monitoring experience...")