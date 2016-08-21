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


import os
import shutil
import unittest
import tempfile
import subprocess

import distro
from mock import patch

from cloudify.mocks import MockCloudifyContext

from .. import tasks


distro_id = distro.id()
PATH = os.path.dirname(__file__)
TEMP_TELEGRAF = os.path.join(tempfile.gettempdir(), 'telegraf')
CONFIG_FILE = os.path.join(TEMP_TELEGRAF, 'telegraf.conf')

dict1_valid = {
    'inputs': {'mem': None,
               'io': None,
               'disk': None,
               'system': None,
               'swap': None,
               'cpu': {'percpu': False,
                       'totalcpu': True,
                       'drop': ['cpu_time']},
               },
    'outputs': {'influxdb':
                {'urls': ['http://localhost:8086'],
                 'database': 'monitoring_telegraf'},
                }
}


def mock_read_file(resource_path):
    with open(resource_path) as f:
        return f.read()


def get_services():
    if distro_id in ('ubuntu', 'debian'):
        output = subprocess.check_output(['ps', '-A'])
    elif distro_id in ('centos', 'redhat'):
        output = subprocess.check_output(['rpm', '-qa'])
    return output


class TestTelegrafPlugin(unittest.TestCase):

    def setUp(self):
        os.mkdir(TEMP_TELEGRAF)

    def tearDown(self):
        # Remove telegraf temp dir
        if os.path.exists(TEMP_TELEGRAF):
            shutil.rmtree(TEMP_TELEGRAF)
        if os.path.exists(os.path.join(tempfile.gettempdir(),
                                       'telegraf.conf')):
            os.remove(os.path.join(tempfile.gettempdir(), 'telegraf.conf'))

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_01_install_service(self):
        """Verify service is available after installation -
        installation file is provided
        """
        output = get_services()
        self.assertNotIn('telegraf', output)

        if distro_id in ('ubuntu', 'debian'):
            tasks.install_telegraf('telegraf_0.12.0-1_amd64.deb', PATH)
        elif distro_id in ('centos', 'redhat'):
            tasks.install_telegraf('telegraf-0.12.0-1.x86_64.rpm', PATH)

        output = get_services()
        self.assertIn('telegraf', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_02_configure_with_inputs_no_file(self, *args):
        """Validate configuration without file -
        rendered correctly and placed on the right place
        """
        tasks.configure('', dict1_valid)
        self.assertTrue(os.path.exists(CONFIG_FILE))
        output = subprocess.check_output(['telegraf',
                                          '-config',
                                          CONFIG_FILE,
                                          '-test'])
        self.assertNotIn('Error', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_03_failed_configure(self, *args):

        dict2_unvalid = {
            'inputs': None,
            'outputs': {'a': {'string': 'string'},
                        'b': None,
                        'c': {'list': ['a', 'b', 'c']}},
            'paths': {'a': {'string': 'string'},
                      'b': {'int': 10},
                      'c': {'list': None}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict2_unvalid)

        dict3_unvalid = {
            'inputs': {'a': None, 'b': {'int': 10},
                       'c': {'list': ['a', 'b', 'c']}},
            'outputs': None,
            'paths': {'a': {'string': 'string'}, 'b': None,
                      'c': {'list': ['a', 'b', 'c']}}
        }
        self.assertRaises(ValueError, tasks.configure, '', dict3_unvalid)

        dict4_unvalid = {
            'inputs': {'string': 'string', 'int': None,
                       'list': ['a', 'b', 'c']},
            'outputs': {'a': {'string': None},
                        'b': {'int': 10, 'list': ['a', 'b', 'c']}},
            'paths': '',
        }
        self.assertRaises(ValueError, tasks.configure, '', dict4_unvalid)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(os.path.join(
               'telegraf_plugin', 'tests', 'example_with_inputs.conf')))
    def test_04_configure_with_inputs_and_file(self, *args):
        """Validate configuration with inputs and file
         rendered correctly and placed on the right place
         """
        dict1_valid = {
            'inputs': {'mem': None,
                       'io': None,
                       'disk': None,
                       'system': None,
                       'swap': None,
                       'cpu': {'percpu': False,
                               'totalcpu': True,
                               'drop': ['cpu_time']},
                       },
            'outputs': {'influxdb':
                        {'urls': ['http://localhost:8086'],
                         'database': 'monitoring_telegraf'},
                        }
        }

        tasks.configure(os.path.join('telegraf_plugin',
                                     'tests',
                                     'example_with_inputs.conf'), dict1_valid)
        self.assertTrue(os.path.exists(CONFIG_FILE))

        output = subprocess.check_output(['telegraf',
                                          '-config',
                                          CONFIG_FILE,
                                          '-test'])
        self.assertNotIn('Error', output)
        self.assertRaises(ValueError, tasks.configure, os.path.join(
                          'telegraf_plugin',
                          'tests',
                          'example_with_inputs.conf'),
                          None)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(
               os.path.join('telegraf_plugin', 'tests', 'example.conf')))
    def test_05_configure_with_file_without_inputs(self, *args):
        """Validate configuration with file without inputs
         rendered correctly and placed on the right place
         """

        tasks.configure(os.path.join(
            'telegraf_plugin', 'tests', 'example.conf'), None)
        self.assertTrue(os.path.exists(CONFIG_FILE))

        output = subprocess.check_output(['telegraf',
                                          '-config',
                                          CONFIG_FILE,
                                          '-test'])
        self.assertNotIn('Error', output)

    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_06_start(self, *args):
        output = tasks.start()
        output = output.aggr_stdout

        self.assertIn('OK', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_07_start_failed_no_file(self, *args):
        self.assertRaises(ValueError, tasks.start)

    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_08_start_failed_with_file(self, *args):
        config = tempfile.NamedTemporaryFile(delete=False).name

        tasks._run('sudo mv {0} /etc/telegraf/telegraf.conf'.format(config))
        output = tasks.start()
        output = output.aggr_stdout
        self.assertIn('FAILED', output)


class TestTelegrafInstall(unittest.TestCase):

    def setUp(self):
        os.mkdir(TEMP_TELEGRAF)

    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def tearDown(self):
        # Remove telegraf temp dir
        tasks._run('sudo dpkg -r telegraf')
        if os.path.exists(TEMP_TELEGRAF):
            shutil.rmtree(TEMP_TELEGRAF)
        if os.path.exists(os.path.join(tempfile.gettempdir(),
                                       'telegraf.conf')):
            os.remove(os.path.join(tempfile.gettempdir(), 'telegraf.conf'))

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(
               os.path.join('telegraf_plugin', 'tests', 'example.conf')))
    def test_11_install_without_inputs(self, *args):
        """
        Verify Install function without inputs - only file
        """
        output = get_services()
        self.assertNotIn('telegraf', output)

        tasks.install(telegraf_config_inputs=None,
                      telegraf_config_file=os.path.join(
                          'telegraf_plugin',
                          'tests',
                          'example.conf'))

        output = get_services()
        self.assertIn('telegraf', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_12_install_with_inputs(self, *args):
        """
        Verify Install function with inputs and default file
        """
        output = get_services()
        self.assertNotIn('telegraf', output)

        tasks.install(telegraf_config_inputs=dict1_valid,
                      telegraf_config_file='')

        output = get_services()
        self.assertIn('telegraf', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    @patch('cloudify.utils.get_manager_file_server_blueprints_root_url',
           return_value='')
    @patch('cloudify.manager.get_resource_from_manager',
           return_value=mock_read_file(os.path.join(
               'telegraf_plugin', 'tests', 'example_with_inputs.conf')))
    def test_13_install_with_file(self, *args):
        """
        Verify Install function with file and inputs
        """
        output = get_services()
        self.assertNotIn('telegraf', output)

        tasks.install(telegraf_config_inputs=dict1_valid,
                      telegraf_config_file=os.path.join(
                          'telegraf_plugin',
                          'tests',
                          'example_with_inputs.conf'))

        output = get_services()
        self.assertIn('telegraf', output)

    @patch('telegraf_plugin.tasks.TELEGRAF_CONFIG_FILE_DEFAULT', CONFIG_FILE)
    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_14_install_path_exists(self, *args):
        """
        Verify Install function with path which already exists
        """

        path = tempfile.NamedTemporaryFile(delete=False)
        self.assertRaises(ValueError, tasks.install,
                          telegraf_config_inputs=dict1_valid,
                          telegraf_config_file='',
                          telegraf_install_path=path.name)
