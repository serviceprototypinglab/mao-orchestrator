import unittest
import audit
import mock


class TestAuditUtilities(unittest.TestCase):
    def test_compare(self):
        list1 = [1, 2]
        list2 = [1, 3]
        self.assertEqual(audit.compare(list1, list2), 1)

    def test_compare_csv_list(self):
        filenames = ['gold/test1.csv', 'gold/test2.csv']
        self.assertEqual(audit.compare_csv_list(filenames), {'gold/test1.csv': 0, 'gold/test2.csv': 0})

    @mock.patch('audit.etcd_client')
    @mock.patch('audit.config', {'DATA_REPOS': {'test': '/home/panos/mao-mao-framework/gold'}})
    def test_submit(self, mock_etcd_client):
        result = audit.submit('test', 'foo', 'bar')
        self.assertEqual(result, '/home/panos/mao-mao-framework/gold/test2.csv')

    @mock.patch('audit.etcd_client')
    def test_audit(self, mock_etcd_client):
        self.assertEqual(audit.audit('gold'), ['test2', 'test1'])


