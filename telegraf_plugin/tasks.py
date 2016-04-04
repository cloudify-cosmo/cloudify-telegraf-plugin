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


# ctx is imported and used in operations
from cloudify import ctx
from cloudify import exceptions
from cloudify import utils


# put the operation decorator on any function that is a task
from cloudify.decorators import operation
import os
import urllib
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
    ctx.logger.info("telegraf.toml was configured...")
    ctx.logger.info("starting telegraf service...")
    start()
    ctx.logger.info("GoodLuck! telegraf service is up! have an awesome monitoring experience...")

@operation
def create():
    # download and install the telegraf servivce
    ctx.instance.runtime_properties['telegraf_path'] = telegraf_path = '/opt/telegraf'

    if not os.path.exists(telegraf_path):
        os.system('sudo mkdir -p {0}'.format(telegraf_path))

    os.chdir(telegraf_path)

    if _platform == "linux" or _platform == "linux2":
        dist = ld.linux_distribution(full_distribution_name=False)[0]
        if dist == 'ubuntu' or dist == 'debian':
            print('downloading telegraf')
            telegraf_file = urllib.urlretrieve('http://get.influxdb.org/telegraf/telegraf_0.11.1-1_amd64.deb')
            print(os.getcwd())
            print(telegraf_file)
            print('telegraf downloaded...installing..')
            os.system('sudo dpkg -i {0}'.format(telegraf_file))
        elif dist == 'centos' or dist == 'redhat':
            urllib.urlretrieve('http://get.influxdb.org/telegraf/telegraf-0.11.1-1.x86_64.rpm', 'telegraf-0.11.1-1.x86_64.rpm')
            os.system('sudo yum localinstall telegraf-0.11.1-1.x86_64.rpm')
    elif _platform == "darwin":
        os.system('brew update')
        os.system('brew install telegraf')
    # no windows distribution

@operation
def configure():
    # generating configuration file with elected outputs & inputs.
    # input is dict\json
    ctx.download_resource_and_render('telegraf.toml', '/etc/opt/telegraf/telegraf.conf')

@operation
def start(config_file=None):
    # starting the telegraf service with the right config file
    # need to validate inputs\outputs correctness?
    if config_file==None:
        config_file = '/etc/opt/telegraf/telegraf.conf'
    if not os.path.isfile(config_file):
        raise exceptions.NonRecoverableError("Config file doesn't exists")

    cmd = 'sudo service telegraf start'
    return_code = call(cmd.split())
    if return_code != 0:
        raise exceptions.NonRecoverableError('Telegraf service failed to start')
