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

    def test_audit(self):
        self.assertEqual(audit.audit('gold'), ['test2', 'test1'])


