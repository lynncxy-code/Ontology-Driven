"""BUG-21: explicit tab selection must not inherit another session's children."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from flask import Flask
import tenant_api as tenant


class TenantContextSwitchTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.cur = MagicMock()
        self.cur.fetchone.return_value = (
            'session', 'user', 1, 'org_a', 'factory_a', 'project_a',
            datetime.now(timezone.utc) + timedelta(hours=1), None,
            'test-user', 'Test User', True, 1,
        )

    def load(self, selection):
        headers = {'X-OntoTwin-Session': 'fixture-token'}
        headers.update({'X-OntoTwin-' + k + '-Id': v for k, v in selection.items()})
        with self.app.test_request_context(headers=headers):
            return tenant._load_session(self.cur)

    def test_switch_org_drops_saved_factory_and_project(self):
        with patch.object(tenant, '_org_role', return_value='admin'), \
             patch.object(tenant, '_factory_allowed') as factory, \
             patch.object(tenant, '_project_allowed') as project:
            result = self.load({'Organization': 'org_b'})
        self.assertEqual(result['organization_id'], 'org_b')
        self.assertIsNone(result['factory_id'])
        self.assertIsNone(result['project_id'])
        factory.assert_not_called()
        project.assert_not_called()

    def test_switch_factory_drops_saved_project(self):
        with patch.object(tenant, '_org_role', return_value='admin'), \
             patch.object(tenant, '_factory_allowed', return_value=(True, 'admin')), \
             patch.object(tenant, '_project_allowed') as project:
            result = self.load({'Organization': 'org_a', 'Factory': 'factory_b'})
        self.assertEqual(result['factory_id'], 'factory_b')
        self.assertIsNone(result['project_id'])
        project.assert_not_called()

    def test_project_only_context_derives_its_own_parents(self):
        with patch.object(tenant, '_org_role') as org, \
             patch.object(tenant, '_factory_allowed') as factory, \
             patch.object(tenant, '_project_allowed', return_value={
                 'organization_id': 'org_b', 'factory_id': 'factory_b'}):
            result = self.load({'Project': 'project_b'})
        self.assertEqual(result['organization_id'], 'org_b')
        self.assertEqual(result['factory_id'], 'factory_b')
        org.assert_not_called()
        factory.assert_not_called()

    def test_no_explicit_context_retains_legacy_session(self):
        result = self.load({})
        self.assertEqual(result['project_id'], 'project_a')

    def test_unauthorized_org_still_forbidden(self):
        with patch.object(tenant, '_org_role', return_value=None):
            with self.assertRaises(tenant.ApiError) as error:
                self.load({'Organization': 'forbidden'})
        self.assertEqual(error.exception.status, 403)

    def test_explicit_mixed_org_factory_still_forbidden(self):
        with patch.object(tenant, '_org_role', return_value='admin'), \
             patch.object(tenant, '_factory_allowed', return_value=(False, None)):
            with self.assertRaises(tenant.ApiError) as error:
                self.load({'Organization': 'org_b', 'Factory': 'factory_a'})
        self.assertEqual(error.exception.status, 403)

    def test_explicit_mixed_project_still_forbidden(self):
        with patch.object(tenant, '_org_role', return_value='admin'), \
             patch.object(tenant, '_project_allowed', return_value={
                 'organization_id': 'org_a', 'factory_id': 'factory_a'}):
            with self.assertRaises(tenant.ApiError) as error:
                self.load({'Organization': 'org_b', 'Project': 'project_a'})
        self.assertEqual(error.exception.status, 403)

    def test_missing_identity_requires_login(self):
        with self.app.test_request_context():
            with self.assertRaises(tenant.ApiError) as error:
                tenant._load_session(self.cur)
        self.assertEqual(error.exception.status, 401)


if __name__ == '__main__':
    unittest.main()
