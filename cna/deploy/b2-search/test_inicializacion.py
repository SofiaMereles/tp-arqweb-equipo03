import importlib.util
from pathlib import Path
import unittest
import psycopg

spec=importlib.util.spec_from_file_location('search_setup',Path(__file__).with_name('inicializar-postgres.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConnectionErrorTests(unittest.TestCase):
    def test_expected_connect_denial_without_sqlstate(self):
        error=psycopg.OperationalError('connection failed: FATAL: permission denied for database "audit_db"\nDETAIL: User does not have CONNECT privilege.')
        self.assertIsNone(error.sqlstate)
        self.assertTrue(module.denied_audit_connection(error))

    def test_expected_sqlstate(self):
        self.assertTrue(module.denied_audit_connection(psycopg.errors.InsufficientPrivilege('CONNECT denied')))

    def test_network_and_authentication_failures_are_not_passes(self):
        for message in ('connection timeout expired','password authentication failed for user "search_owner"',
                        'could not translate host name "postgres" to address',
                        'permission denied for database "other_db"'):
            with self.subTest(message=message):
                self.assertFalse(module.denied_audit_connection(psycopg.OperationalError(message)))

    def test_diagnostic_redacts_secret_values(self):
        message=module.redact('failed fake-admin-secret and fake-search-secret', ['fake-admin-secret','fake-search-secret'])
        self.assertNotIn('fake-admin-secret',message)
        self.assertNotIn('fake-search-secret',message)


if __name__=='__main__':
    unittest.main()
