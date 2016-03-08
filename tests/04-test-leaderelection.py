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

    def test_leader_election_failover(self):
        unit = self.d.sentry['pdi'][0].info
        message = unit['workload-status'].get('message')
        ip = message.split(':', 1)[-1]
        self.d.add_unit('pdi', 2)
        # self.d.sentry.wait_for_messages
        # ({'pdi': 'leadership has changed, scheduling restart'})
        self.d.sentry.wait_for_messages(
            {'pdi': 'Initializing Leadership Layer'
             ' (is follower)'})
        # message2 = unit['workload-status'].get('message')
        ip2 = message.split(':', 1)[-1]

        self.assertNotEqual(ip, ip2)


if __name__ == '__main__':
    unittest.main()
