#!/usr/bin/env python3

import amulet
import unittest
from subprocess import check_call


class TestDeploy(unittest.TestCase):
    """
    Deployment test for the Pentaho Data Integration charm.

    """

    @classmethod
    def setUpClass(cls):
        cls.d = amulet.Deployment(series='trusty')
        cls.d.add('pdi', 'pentahodataintegration')
        cls.d.add('openjdk', 'cs:~kwmonroe/trusty/openjdk')
        cls.d.relate('pdi:java', 'openjdk:java')
        cls.d.setup(timeout=900)
        cls.d.sentry.wait(timeout=1800)
        cls.unit = cls.d.sentry['pdi'][0]
        cls.d.expose('pdi')

    def test_running_carte(self):
        output, code = self.unit.run('pgrep -f org.pentaho.di.www.Carte '
                                     '|grep -v pgrep')
        print(output)
        if code != 0:
            message = 'Carte is not running!'
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_stop_start_carte(self):

        output, code = self.unit.run('pgrep -af org.pentaho.di.www.Carte '
                                     '| grep -v pgrep')
        print(output)
        if code != 0:
            message = 'Carte is not running!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'run_carte': False})
        self.d.sentry.wait()
        output2, code2 = self.unit.run('pgrep -af org.pentaho.di.www.Carte '
                                       '| grep -v pgrep')
        print(output2)
        if code2 == 0:
            message = 'Carte is still running!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'run_carte': True})
        self.d.sentry.wait()
        output3, code3 = self.unit.run('pgrep -af org.pentaho.di.www.Carte  '
                                       '|grep -v pgrep')
        print(output3)
        if code != 0:
            message = 'Carte is not running!'
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_change_password_carte(self):

        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:cluster')
        print(output)
        if code != 0:
            message = 'Could not login to carte!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'carte_password': 'mynewpassword'})
        self.d.sentry.wait()
        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:cluster')
        print(output)
        if code == 0:
            message = 'Logged in with the old login details'
            amulet.raise_status(amulet.FAIL, msg=message)

        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:mynewpassword')
        print(output)
        if code != 0:
            message = 'Could not login to carte with new password!'
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_change_carte_port(self):
        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:cluster')
        print(output)
        if code != 0:
            message = 'Could not login to carte!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'carte_port': '9998'})
        self.d.sentry.wait()
        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:cluster')
        print(output)
        if code == 0:
            message = 'Logged in with the old port'
            amulet.raise_status(amulet.FAIL, msg=message)

        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9998 --user cluster:cluster')
        print(output)
        if code != 0:
            message = 'Could not login to carte with new port!'
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_run_transformation_action(self):
        check_call(['juju', 'scp',
                    'tests/files/test_transformation.ktr', 'pdi/0:/tmp'])
        id = self.d.action_do('pdi/0',
                              'runtransformation',
                              {"path": '/tmp/test_transformation.ktr'})
        self.assertEqual({'outcome': 'ETL execution finished'},
                         self.d.action_fetch(id))

    def test_run_job_action(self):
        check_call(['juju', 'scp',
                    'tests/files/test_transformation.ktr', 'pdi/0:/tmp'])
        check_call(['juju', 'scp',
                    'tests/files/test_job.kjb', 'pdi/0:/tmp'])

        id = self.d.action_do('pdi/0',
                              'runjob', {"path": '/tmp/test_job.ktr'})
        self.assertEqual({'outcome': 'ETL execution finished'},
                         self.d.action_fetch(id))

    def test_schedule_transformation_action(self):
        check_call(['juju', 'scp',
                    'tests/files/test_transformation.ktr', 'pdi/0:/tmp'])
        id = self.d.action_do('pdi/0',
                              'runtransformation',
                              {"path": '/tmp/test_transformation.ktr',
                               "cron-entry": '0 0 * * *'})
        self.assertEqual({'outcome': 'ETL scheduled'}, self.d.action_fetch(id))

    def test_schedule_job_action(self):
        check_call(['juju', 'scp',
                    'tests/files/test_transformation.ktr', 'pdi/0:/tmp'])
        id = self.d.action_do('pdi/0',
                              'runtransformation',
                              {"path": '/tmp/test_transformation.kjb',
                               "cron-entry": '0 0 * * *'})
        self.assertEqual({'outcome': 'ETL scheduled'}, self.d.action_fetch(id))

    def test_leader_election_failover(self):
        unit = self.d.sentry['pdi'][0].info
        message = unit['workload-status'].get('message')
        ip = message.split(':', 1)[-1]
        self.d.add_unit('pdi', 2)
        self.d.sentry.wait_for_messages({'pdi': 'leadership has changed, scheduling restart'})
        message2 = unit['workload-status'].get('message')
        ip2 = message.split(':', 1)[-1]

        self.assertNotEqual(ip, ip2)


        # find leader
        # check configs
        # kill leader
        # check configs


if __name__ == '__main__':
    unittest.main()
