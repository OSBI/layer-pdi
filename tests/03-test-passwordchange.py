#!/usr/bin/env python3

import amulet
import unittest


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

if __name__ == '__main__':
    unittest.main()
