"""
Unit tests for sio_sdk — collect_instances and collect_statistics_v5.
Uses a mock REST client; no network access required.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sio_sdk


def make_client(get_json_response=None, post_json_response=None):
    client = MagicMock()
    if get_json_response is not None:
        client.get_json.return_value = get_json_response
    if post_json_response is not None:
        client.post_json.return_value = post_json_response
    return client


# Minimal /api/instances payload used across several tests
INSTANCES_PAYLOAD = {
    'System': {
        'id': 'sys-001',
        'name': 'test-cluster',
        'links': [],
    },
    'storageNodeList': [
        {
            'id': 'sn-001', 'name': 'SN-1',
            'links': [
                {'rel': '/api/parent/relationship/protectionDomainId',
                 'href': '/api/instances/ProtectionDomain:pdo-001'}
            ]
        }
    ],
    'protectionDomainList': [
        {
            'id': 'pdo-001', 'name': 'PD-1',
            'links': []
        }
    ],
    'sdtList': [
        {
            'id': 'sdt-001', 'name': 'sdt_node-1',
            'links': [
                {'rel': '/api/parent/relationship/protectionDomainId',
                 'href': '/api/instances/ProtectionDomain:pdo-001'}
            ]
        }
    ],
}


class TestCollectInstances(unittest.TestCase):

    def setUp(self):
        self.client = make_client(get_json_response=INSTANCES_PAYLOAD)
        self.instances, self.relations = sio_sdk.collect_instances(self.client)

    def test_system_collected(self):
        self.assertIn('System', self.instances)
        self.assertEqual(len(self.instances['System']), 1)
        self.assertEqual(self.instances['System'][0]['id'], 'sys-001')

    def test_storage_node_list_parsed(self):
        self.assertIn('StorageNode', self.instances)
        self.assertEqual(len(self.instances['StorageNode']), 1)
        self.assertEqual(self.instances['StorageNode'][0]['id'], 'sn-001')

    def test_protection_domain_collected(self):
        self.assertIn('ProtectionDomain', self.instances)
        self.assertEqual(self.instances['ProtectionDomain'][0]['id'], 'pdo-001')

    def test_sdt_collected(self):
        self.assertIn('Sdt', self.instances)
        self.assertEqual(len(self.instances['Sdt']), 1)
        self.assertEqual(self.instances['Sdt'][0]['id'], 'sdt-001')

    def test_parent_relation_built(self):
        # sn-001 should have pdo-001 as ProtectionDomain parent
        parents = self.relations['parents']
        self.assertIn('sn-001', parents)
        self.assertIn('ProtectionDomain', parents['sn-001'])
        self.assertIn('pdo-001', parents['sn-001']['ProtectionDomain'])

    def test_children_relation_built(self):
        children = self.relations['children']
        self.assertIn('pdo-001', children)
        self.assertIn('StorageNode', children['pdo-001'])
        self.assertIn('sn-001', children['pdo-001']['StorageNode'])

    def test_sdt_parent_relation(self):
        parents = self.relations['parents']
        self.assertIn('sdt-001', parents)
        self.assertIn('ProtectionDomain', parents['sdt-001'])
        self.assertIn('pdo-001', parents['sdt-001']['ProtectionDomain'])

    def test_type_name_capitalised(self):
        # 'storageNodeList' -> 'StorageNode', 'sdtList' -> 'Sdt'
        self.assertNotIn('storageNodeList', self.instances)
        self.assertNotIn('sdtList', self.instances)

    def test_list_suffix_stripped(self):
        self.assertIn('StorageNode', self.instances)
        self.assertIn('Sdt', self.instances)


class TestCollectStatisticsV5(unittest.TestCase):

    def _make_query_response(self, resource_id, metric_name, value):
        return {
            'resources': [{
                'id': resource_id,
                'metrics': [
                    {'name': metric_name, 'values': [value]}
                ]
            }]
        }

    def test_basic_metric_collected(self):
        v5_metrics = {'System': {'host_read_iops': ('iops', 'host', 'read')}}
        v5_resource_type = {'System': 'system'}
        client = make_client(post_json_response=self._make_query_response('sys-001', 'host_read_iops', 42))
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertIn('System', stats)
        self.assertIn('sys-001', stats['System'])
        self.assertEqual(stats['System']['sys-001']['host_read_iops'], 42)

    def test_multiple_metrics_in_single_call(self):
        v5_metrics = {
            'System': {
                'host_read_iops':  ('iops', 'host', 'read'),
                'host_write_iops': ('iops', 'host', 'write'),
            }
        }
        v5_resource_type = {'System': 'system'}
        response = {
            'resources': [{
                'id': 'sys-001',
                'metrics': [
                    {'name': 'host_read_iops',  'values': [10]},
                    {'name': 'host_write_iops', 'values': [20]},
                ]
            }]
        }
        client = make_client(post_json_response=response)
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertEqual(stats['System']['sys-001']['host_read_iops'], 10)
        self.assertEqual(stats['System']['sys-001']['host_write_iops'], 20)

    def test_multiple_resource_instances(self):
        v5_metrics = {'StorageNode': {'raw_total': (None, 'raw_total', '')}}
        v5_resource_type = {'StorageNode': 'storage_node'}
        response = {
            'resources': [
                {'id': 'sn-001', 'metrics': [{'name': 'raw_total', 'values': [100]}]},
                {'id': 'sn-002', 'metrics': [{'name': 'raw_total', 'values': [200]}]},
            ]
        }
        client = make_client(post_json_response=response)
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertEqual(stats['StorageNode']['sn-001']['raw_total'], 100)
        self.assertEqual(stats['StorageNode']['sn-002']['raw_total'], 200)

    def test_empty_values_list_stores_none(self):
        v5_metrics = {'System': {'host_read_iops': ('iops', 'host', 'read')}}
        v5_resource_type = {'System': 'system'}
        response = {
            'resources': [{'id': 'sys-001', 'metrics': [{'name': 'host_read_iops', 'values': []}]}]
        }
        client = make_client(post_json_response=response)
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertIsNone(stats['System']['sys-001']['host_read_iops'])

    def test_api_error_skips_type(self):
        v5_metrics = {
            'System':      {'host_read_iops': ('iops', 'host', 'read')},
            'StorageNode': {'raw_total': (None, 'raw_total', '')},
        }
        v5_resource_type = {'System': 'system', 'StorageNode': 'storage_node'}

        def post_side_effect(path, body):
            if body['resource_type'] == 'system':
                raise sio_sdk.SioRestException('query failed')
            return {'resources': [{'id': 'sn-001', 'metrics': [{'name': 'raw_total', 'values': [99]}]}]}

        client = MagicMock()
        client.post_json.side_effect = post_side_effect
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertNotIn('System', stats)
        self.assertIn('StorageNode', stats)

    def test_unknown_resource_type_skipped(self):
        v5_metrics = {'Ghost': {'some_metric': (None, 'some_metric', '')}}
        v5_resource_type = {}  # no mapping for 'Ghost'
        client = make_client()
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertEqual(stats, {})
        client.post_json.assert_not_called()

    def test_empty_metrics_def_skipped(self):
        v5_metrics = {'System': {}}
        v5_resource_type = {'System': 'system'}
        client = make_client()
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertEqual(stats, {})
        client.post_json.assert_not_called()

    def test_correct_resource_type_sent_in_body(self):
        v5_metrics = {'StorageNode': {'raw_total': (None, 'raw_total', '')}}
        v5_resource_type = {'StorageNode': 'storage_node'}
        client = make_client(post_json_response={'resources': []})
        sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        call_body = client.post_json.call_args[0][1]
        self.assertEqual(call_body['resource_type'], 'storage_node')
        self.assertIn('raw_total', call_body['metrics'])

    def test_sdt_metrics_collected(self):
        v5_metrics = {
            'Sdt': {
                'avg_controller_to_host_latency': ('latency', 'controller_to_host', ''),
                'avg_host_to_controller_latency': ('latency', 'host_to_controller', ''),
            }
        }
        v5_resource_type = {'Sdt': 'sdt'}
        response = {
            'resources': [{
                'id': 'sdt-001',
                'metrics': [
                    {'name': 'avg_controller_to_host_latency', 'values': [6]},
                    {'name': 'avg_host_to_controller_latency', 'values': [441]},
                ]
            }]
        }
        client = make_client(post_json_response=response)
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertIn('Sdt', stats)
        self.assertEqual(stats['Sdt']['sdt-001']['avg_controller_to_host_latency'], 6)
        self.assertEqual(stats['Sdt']['sdt-001']['avg_host_to_controller_latency'], 441)

    def test_only_first_timestamp_value_stored(self):
        v5_metrics = {'System': {'host_read_iops': ('iops', 'host', 'read')}}
        v5_resource_type = {'System': 'system'}
        response = {
            'resources': [{
                'id': 'sys-001',
                'metrics': [{'name': 'host_read_iops', 'values': [10, 20, 30]}]
            }]
        }
        client = make_client(post_json_response=response)
        stats = sio_sdk.collect_statistics_v5(client, v5_metrics, v5_resource_type)
        self.assertEqual(stats['System']['sys-001']['host_read_iops'], 10)


if __name__ == '__main__':
    unittest.main()
