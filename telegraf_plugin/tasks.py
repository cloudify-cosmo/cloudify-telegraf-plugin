########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
########

import os
import sys
import subprocess

import ld
import shlex

# ctx is imported and used in operations
from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation


@operation
def install(telegraf_config, config_file, telegraf_path, download_url, **kwargs):
    if 'linux' not in sys._platform:
        raise exceptions.NonRecoverableError('Error! Telegraf-plugin is available on linux distribution only')

    download_and_install(telegraf_path, download_url)
    configure(telegraf_config, config_file)


@operation
def start(config_file='', **kwargs):
    ctx.logger.info('Starting telegraf service...')
    if not config_file:
        config_file = '/etc/telegraf/telegraf.conf'
    if not os.path.isfile(config_file):
        raise exceptions.NonRecoverableError("Config file doesn't exists")

    cmd = 'sudo service telegraf restart'
    return_code = call(cmd, shell=True)
    if return_code != 0:
        raise exceptions.NonRecoverableError(
            'Telegraf service failed to start')
    ctx.logger.info('GoodLuck! Telegraf service is up!\
                    Have an awesome monitoring experience...')


def download_and_install(telegraf_path='', download_url='', **kwargs):
    ctx.logger.info('Installing telegraf...')
    if not telegraf_path:
        telegraf_path = '/opt/telegraf'

    ctx.instance.runtime_properties['telegraf_path'] = telegraf_path

    if not os.path.exists(telegraf_path):
        cmd = 'sudo mkdir -p {0}'.format(telegraf_path)
        subprocess.call(shlex.split(cmd))

    os.chdir(telegraf_path)

    dist = ld.id()
    if dist in ('ubuntu', 'debian'):
        if not download_url:
            download_url = 'http://get.influxdb.org/telegraf/telegraf_0.12.0-1_amd64.deb'
        ctx.logger.info('Downloading telegraf...')
        subprocess.call(shlex.split('sudo wget {0}'.format(download_url)))
        ctx.logger.info('Telegraf downloaded...installing..')
        installation_file = download_url.rsplit('/', 1)[-1]
        cmd = 'sudo dpkg -i {0}'.format(installation_file)
        subprocess.call(shlex.split(cmd))
        # if return_code != 0:
        #     raise exceptions.NonRecoverableError(
        #         'Unable to install Telegraf service')
    elif dist in ('centos', 'redhat'):
        if not download_url:
            download_url = 'sudo wget http://get.influxdb.org/telegraf/telegraf-0.12.0-1.x86_64.rpm'
        subprocess.call(shlex.split('sudo wget {0}'.format(download_url)))
        ctx.logger.info('Telegraf downloaded...installing..')
        installation_file = download_url.rsplit('/', 1)[-1]
        cmd = 'sudo yum localinstall {0}'.format(installation_file)
        subprocess.call(shlex.split(cmd))
    ctx.logger.info('Telegraf service was installed...')


def configure(telgraf_config, config_file='',  **kwargs):
    ctx.logger.info('Configuring telegraf.toml...')

    if not config_file:
        config_file = ctx.download_resource_and_render('telegraf.conf', template_variables=telgraf_config)
    cmd = 'sudo mv {0} /etc/telegraf/telegraf.conf'.format(config_file)
    subprocess.Popen(cmd, shell=True)
    ctx.logger.info('telegraf.conf was configured...')
