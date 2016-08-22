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
import shlex
import tempfile
import subprocess
import pkg_resources

import jinja2
import distro
import requests

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

import telegraf_plugin

dist = distro.id()
TELEGRAF_CONFIG_FILE_DEFAULT = os.path.join(
    '/', 'etc', 'telegraf', 'telegraf.conf')
TELEGRAF_PATH_DEFAULT = os.path.join('/', 'opt', 'telegraf')


@operation
def install(telegraf_config_inputs,
            telegraf_config_file='',
            telegraf_install_path='',
            download_url='', **kwargs):
    """Installation operation.

    Downloading and installing telegraf packacge - default version is 0.12.0.
    Default installation dir is set to /opt/telegraf.
    Only linux distributions are supported.
    """
    if 'linux' not in sys.platform:
        raise exceptions.NonRecoverableError(
            'Error! Telegraf-plugin is available on linux distribution only')

    if not telegraf_install_path:
        telegraf_install_path = TELEGRAF_PATH_DEFAULT
    if os.path.isfile(telegraf_install_path):
        raise ValueError(
            format("Error! {0} file already exists, can't create dir.",
                   telegraf_install_path))

    installation_file = download_telegraf(download_url, telegraf_install_path)
    install_telegraf(installation_file, telegraf_install_path)
    configure(telegraf_config_file, telegraf_config_inputs)


@operation
def start(**kwargs):
    """Start operation call for telegraf service,
    with telegraf_plugin configuration file.

    If telegraf service was already running -
    it will restart it and will use updated configuration file.
    """
    ctx.logger.info('Starting telegraf service...')
    telegraf_config_file = TELEGRAF_CONFIG_FILE_DEFAULT
    if not os.path.isfile(telegraf_config_file):
        raise ValueError(
            "Can't start the service. Wrong config file provided")

    if os.path.exists('/usr/bin/systemctl'):
        proc = _run('sudo systemctl restart telegraf')
    else:
        proc = _run('sudo service telegraf restart')

    ctx.logger.info(
        'GoodLuck! Telegraf service is up!'
        'Have an awesome monitoring experience...')
    return proc.aggr_stdout


def download_telegraf(download_url='', telegraf_install_path='', **kwargs):
    """Downloading telegraf package form your desire url.

    Default url set to be version 0.12.0
    anf downloaded from official influxdb site.
    """

    if not os.path.exists(telegraf_install_path):
        _run('sudo mkdir -p {0}'.format(telegraf_install_path))

    ctx.logger.info('Downloading telegraf...')

    if not download_url:
        if dist in ('ubuntu', 'debian'):
            download_url = 'http://get.influxdb.org/telegraf/' + \
                           'telegraf_0.12.0-1_amd64.deb'
        elif dist in ('centos', 'redhat'):
            download_url = 'http://get.influxdb.org/telegraf/' + \
                           'telegraf-0.12.0-1.x86_64.rpm'
        else:
            raise exceptions.NonRecoverableError(
                '''Error! distribution is not supported.
                Ubuntu, Debian, Centos and Redhat are supported currently''')
    installation_file = _download_file(download_url, telegraf_install_path)

    ctx.logger.info('Telegraf downloaded.')
    return installation_file


def install_telegraf(installation_file, telegraf_install_path, **kwargs):
    """Depacking telegraf package."""
    ctx.logger.info('Installing telegraf...')

    if dist in ('ubuntu', 'debian'):
        install_cmd = 'sudo dpkg -i {0}'.format(
            os.path.join(telegraf_install_path, installation_file))
    elif dist in ('centos', 'redhat'):
        install_cmd = 'sudo yum localinstall -y {0}'.format(
            os.path.join(telegraf_install_path, installation_file))
    else:
        raise exceptions.NonRecoverableError(
            '''Error! distribution is not supported.
            Ubuntu, Debian, Centos and Redhat are supported currently''')
    _run(install_cmd)
    ctx.logger.info('Telegraf service was installed...')


def configure(telegraf_config_file='', telgraf_config='', **kwargs):
    """Generating configuration file from your own desire destination
    or from telegraf_plugin telegraf.conf file.

    Rendering your inputs/outputs definitions.
    """
    ctx.logger.info('Configuring Telegraf...')
    dest_file = os.path.join(tempfile.gettempdir(), 'telegraf.conf')
    if telegraf_config_file:
        try:
            ctx.download_resource_and_render(telegraf_config_file,
                                             dest_file,
                                             telgraf_config)
        except:
            raise ValueError(
                "wrong inputs provided! can't redner configuration file")
    else:
        telegraf_config_file = pkg_resources.resource_string(
            telegraf_plugin.__name__, 'resources/telegraf.conf')
        configuration = jinja2.Template(telegraf_config_file)
        try:
            with open(dest_file, 'w') as f:
                f.write(configuration.render(telgraf_config))
        except:
            raise ValueError(
                "wrong inputs provided! can't redner configuration file")

    _run('sudo mv {0} {1}'.format(dest_file, TELEGRAF_CONFIG_FILE_DEFAULT))

    try:
        _run('telegraf -config {0} -test'.format(
            TELEGRAF_CONFIG_FILE_DEFAULT))
    except:
        raise ValueError(
            "wrong inputs prodided! configuration file is unvalid")
    ctx.logger.info('telegraf.conf was configured...')


def _download_file(url, destination):
    try:
        filename = url.split('/')[-1]
    except:
        raise ValueError("wrong url provided! can't _download_file")
    temp_dir = tempfile.gettempdir()
    local_filename = os.path.join(temp_dir, filename)
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as temp_file:
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                temp_file.write(chunk)
    _run('sudo mv {0} {1}'.format(local_filename, os.path.join(destination,
                                                               filename)))
    return filename


def _run(command):
    if isinstance(command, str):
        command = shlex.split(command)
    stderr = subprocess.PIPE
    stdout = subprocess.PIPE

    ctx.logger.debug('Running: {0}'.format(command))
    proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    proc.aggr_stdout, proc.aggr_stderr = proc.communicate()
    if proc.returncode != 0:
        command_str = ' '.join(command)
        ctx.logger.error('Failed running command: {0} ({1}).'.format(
            command_str, proc.aggr_stderr))
        sys.exit(1)
    return proc
