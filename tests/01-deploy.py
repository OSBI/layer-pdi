#!/usr/bin/env python3

import unittest
import amulet


class TestDeploy(unittest.TestCase):
    """
    Deployment test for the Pentaho Data Integration charm.

    """

    @classmethod
    def setUpClass(cls):
        cls.d = amulet.Deployment(series='trusty')
        cls.d.add('pdi', 'cs:~f-tom-n/trusty/pentahodataintegration-1')
        cls.d.add('openjdk', 'cs:~kwmonroe/trusty/openjdk-5')
        cls.d.relate('pdi:java', 'openjdk:java')
        cls.d.setup(timeout=900)
        cls.d.sentry.wait(timeout=1800)
        cls.unit = cls.d.sentry['pdi'][0]
        cls.d.expose('pdi')

    def test_running_carte(self):
        commands = ['bzr version', 'cvs version',
                    'git version', 'svn --version --quiet']
        for cmd in commands:
            print("running {}".format(cmd))
            output, rc = self.unit.run(cmd)
            print("output from cmd: {}".format(output))
            assert rc == 0, "Unexpected return code: {}".format(rc)

    def test_stop_start_carte(self):

        output, code = self.unit.run('pgrep -f org.pentaho.di.www.Carte')
        print(output)
        if code != 0:
            message = 'Carte is not running!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'run_carte': False})

        output, code = self.unit.run('pgrep -f org.pentaho.di.www.Carte')
        print(output)
        if code == 0:
            message = 'Carte is still running!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'run_carte': True})

        output, code = self.unit.run('pgrep -f org.pentaho.di.www.Carte')
        print(output)
        if code != 0:
            message = 'Carte is not running!'
            amulet.raise_status(amulet.FAIL, msg=message)

    def change_password_carte(self):

        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:cluster')
        print(output)
        if code != 0:
            message = 'Could not login to carte!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'carte_password': 'mynewpassword'})

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

    def change_carte_port(self):
        output, code = self.unit.run('curl --fail ' +
                                     self.unit.info['public-address'] +
                                     ':9999 --user cluster:cluster')
        print(output)
        if code != 0:
            message = 'Could not login to carte!'
            amulet.raise_status(amulet.FAIL, msg=message)

        self.d.configure('pdi', {'carte_port': '9998'})

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

            # def run_transformation_action:
            # upload transformation
            # check transformation runs

            # def run_job_action:
            # upload job
            # check job runs

            # def schedule_transformation_action:
            # upload transformation
            # schedule
            # check scheduled
            # unschedule
            # check unscheduled

            # def schedule_job_action:
            # upload job
            # schedule
            # check scheduled
            # unschedule
            # check unscheduled
            # def test_leader_election_failover:
            # spin up 3 nodes
            # find leader
            # check configs
            # kill leader
            # check configs

    def test_java(self):
        cmd = "java -version 2>&1"
        print("running {}".format(cmd))
        output, rc = self.unit.run(cmd)
        print("output from cmd: {}".format(output))
        assert rc == 0, "Unexpected return code: {}".format(rc)


if __name__ == '__main__':
    unittest.main()
