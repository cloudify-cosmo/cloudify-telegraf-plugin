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

import distro
from mock import patch

from cloudify.mocks import MockCloudifyContext

from .. import tasks


disto_id = distro.id()
TEMP_TELEGRAF = os.path.join(tempfile.gettempdir(), 'telegraf')


class TesttelegrafPlugin(unittest.TestCase):

    def setUp(self):
        os.mkdir(TEMP_TELEGRAF)

    def tearDown(self):
        # Remove telegraf temp dir
        if os.path.exists(TEMP_TELEGRAF):
            shutil.rmtree(TEMP_TELEGRAF)

    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_telegraf(self):
        '''Test download_telegraf function
        '''

        filename = tasks.download_telegraf('', TEMP_TELEGRAF)
        if disto_id in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'telegraf_0.12.0-1_amd64.deb')
        elif disto_id in ('centos', 'redhat'):
            self.assertEqual(filename, 'telegraf-0.12.0-1.x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_TELEGRAF, filename)))

    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_telegraf_path_not_exists(self):
        '''Test download - verify nothing downloaded
        '''
        filename = tasks.download_telegraf('', TEMP_TELEGRAF)

        if disto_id in ('ubuntu', 'debian'):
            self.assertEqual(filename, 'telegraf_0.12.0-1_amd64.deb')
        elif disto_id in ('centos', 'redhat'):
            self.assertEqual(filename, 'telegraf-0.12.0-1.x86_64.rpm')
        self.assertTrue(os.path.exists(os.path.join(TEMP_TELEGRAF, filename)))

    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_file(self):
        '''Test download -  verify file exists after download
        '''

        filename = tasks._download_file(
            'http://get.influxdb.org/telegraf/' +
            'telegraf_0.12.0-1_amd64.deb',
            TEMP_TELEGRAF)
        self.assertEqual(filename, 'telegraf_0.12.0-1_amd64.deb')
        self.assertTrue(os.path.exists(os.path.join(TEMP_TELEGRAF, filename)))

    @patch('telegraf_plugin.tasks.TELEGRAF_PATH_DEFAULT', TEMP_TELEGRAF)
    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_download_file_failed(self):
        '''Test download - verify nothing downloaded
        '''

        self.assertRaises(ValueError, tasks._download_file, None, None)

    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_run_command(self):
        cmd = 'mkdir /tmp/test'
        output = tasks._run(cmd)
        self.assertEqual(output.returncode, 0)

    @patch('telegraf_plugin.tasks.ctx', MockCloudifyContext())
    def test_run_command_failed(self):
        self.assertRaises(OSError, tasks._run, "invalid command")
        self.assertRaises(SystemExit, tasks._run, "mkdir /opt/test")
