import unittest
import differ
import mock


class TestSpikeDetection(unittest.TestCase):
    @mock.patch('differ.etcd_client')
    def test_detect(self, mock_etcd_client):
        result = differ.diff('/home/panos/mao-mao-framework/gold/differ', 'test')
        self.assertTrue(result['spike'])

