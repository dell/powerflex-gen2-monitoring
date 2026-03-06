"""
Unit tests for siometrics.py tag formatter functions.
Tests all fmt_* functions with minimal synthetic instance/relation fixtures.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import siometrics


def make_relations(child_id, child_type, parent_id, parent_type):
    """Build a minimal relations dict with one parent link."""
    return {
        'children': {parent_id: {child_type: [child_id]}},
        'parents':  {child_id:  {parent_type: [parent_id]}},
    }


PDO = {'id': 'pdo-001', 'name': 'PD-1', 'links': []}
PDO2 = {'id': 'pdo-002', 'name': 'PD-2', 'links': []}
STO = {'id': 'sto-001', 'name': 'SP-1', 'links': []}
SN  = {'id': 'sn-001',  'name': 'SN-1', 'links': []}


class TestFmtStorageNode(unittest.TestCase):

    def setUp(self):
        self.node = {'id': 'sn-001', 'name': 'SN-1', 'links': []}
        self.instances = {'ProtectionDomain': [PDO]}
        self.relations = make_relations('sn-001', 'StorageNode', 'pdo-001', 'ProtectionDomain')

    def test_returns_expected_keys(self):
        result = siometrics.fmt_StorageNode(self.node, self.instances, self.relations)
        self.assertIn('sn_name', result)
        self.assertIn('sn_id', result)
        self.assertIn('pdo_name', result)
        self.assertIn('pdo_id', result)

    def test_values(self):
        result = siometrics.fmt_StorageNode(self.node, self.instances, self.relations)
        self.assertEqual(result['sn_name'], 'SN-1')
        self.assertEqual(result['sn_id'], 'sn-001')
        self.assertEqual(result['pdo_name'], 'PD-1')
        self.assertEqual(result['pdo_id'], 'pdo-001')

    def test_parent_not_found_raises(self):
        bad_relations = {'children': {}, 'parents': {'sn-001': {'ProtectionDomain': ['no-such-pdo']}}}
        with self.assertRaises(Exception):
            siometrics.fmt_StorageNode(self.node, self.instances, bad_relations)

    def test_equals_in_name_escaped(self):
        node = {'id': 'sn-001', 'name': 'SN=1', 'links': []}
        result = siometrics.fmt_StorageNode(node, self.instances, self.relations)
        self.assertIn('\\=', result['sn_name'])
        self.assertNotIn('SN=1', result['sn_name'])


class TestFmtDevice(unittest.TestCase):

    def setUp(self):
        self.device = {
            'id': 'dev-001', 'name': 'dev1',
            'deviceCurrentPathName': '/dev/sda',
            'links': []
        }
        self.sn = {'id': 'sn-001', 'name': 'SN-1', 'links': []}
        self.instances = {
            'StorageNode': [self.sn],
            'ProtectionDomain': [PDO],
        }
        self.relations = {
            'children': {},
            'parents': {
                'dev-001': {'StorageNode': ['sn-001']},
                'sn-001':  {'ProtectionDomain': ['pdo-001']},
            }
        }

    def test_returns_expected_keys(self):
        result = siometrics.fmt_Device(self.device, self.instances, self.relations)
        for key in ('dev_name', 'dev_id', 'dev_path', 'sn_name', 'sn_id', 'pdo_name', 'pdo_id'):
            self.assertIn(key, result)

    def test_dev_path_strips_dev_prefix(self):
        result = siometrics.fmt_Device(self.device, self.instances, self.relations)
        self.assertEqual(result['dev_path'], 'sda')

    def test_values(self):
        result = siometrics.fmt_Device(self.device, self.instances, self.relations)
        self.assertEqual(result['dev_name'], 'dev1')
        self.assertEqual(result['sn_name'], 'SN-1')
        self.assertEqual(result['pdo_name'], 'PD-1')

    def test_none_name_falls_back_to_id(self):
        device = dict(self.device, name=None)
        result = siometrics.fmt_Device(device, self.instances, self.relations)
        self.assertEqual(result['dev_name'], 'dev-001')

    def test_v5_storage_node_key(self):
        # v5 uses 'StorageNode' not 'Sds'
        result = siometrics.fmt_Device(self.device, self.instances, self.relations)
        self.assertEqual(result['sn_id'], 'sn-001')


class TestFmtVolume(unittest.TestCase):

    def setUp(self):
        self.volume = {
            'id': 'vol-001', 'name': 'vol1',
            'volumeType': 'ThinProvisioned',
            'links': []
        }
        self.sto = {'id': 'sto-001', 'name': 'SP-1', 'links': []}
        self.instances = {
            'StoragePool': [self.sto],
            'ProtectionDomain': [PDO],
        }
        self.relations = {
            'children': {},
            'parents': {
                'vol-001': {'StoragePool': ['sto-001']},
                'sto-001': {'ProtectionDomain': ['pdo-001']},
            }
        }

    def test_returns_expected_keys(self):
        result = siometrics.fmt_Volume(self.volume, self.instances, self.relations)
        for key in ('vol_name', 'vol_id', 'vol_type', 'sto_name', 'sto_id', 'pdo_name', 'pdo_id'):
            self.assertIn(key, result)

    def test_volume_type_thin_provisioned_mapped(self):
        result = siometrics.fmt_Volume(self.volume, self.instances, self.relations)
        self.assertEqual(result['vol_type'], 'BaseVolume')

    def test_volume_type_snapshot_mapped(self):
        vol = dict(self.volume, volumeType='Snapshot')
        result = siometrics.fmt_Volume(vol, self.instances, self.relations)
        self.assertEqual(result['vol_type'], 'ThinClone')

    def test_volume_type_readonly_snapshot_passthrough(self):
        vol = dict(self.volume, volumeType='ReadOnlySnapshot')
        result = siometrics.fmt_Volume(vol, self.instances, self.relations)
        self.assertEqual(result['vol_type'], 'ReadOnlySnapshot')

    def test_volume_type_unknown_passthrough(self):
        vol = dict(self.volume, volumeType='SomeNewType')
        result = siometrics.fmt_Volume(vol, self.instances, self.relations)
        self.assertEqual(result['vol_type'], 'SomeNewType')


class TestFmtStoragePool(unittest.TestCase):

    def setUp(self):
        self.pool = {'id': 'sto-001', 'name': 'SP-1', 'links': []}
        self.instances = {'ProtectionDomain': [PDO]}
        self.relations = make_relations('sto-001', 'StoragePool', 'pdo-001', 'ProtectionDomain')

    def test_returns_expected_keys(self):
        result = siometrics.fmt_StoragePool(self.pool, self.instances, self.relations)
        for key in ('sto_name', 'sto_id', 'pdo_name', 'pdo_id'):
            self.assertIn(key, result)

    def test_values(self):
        result = siometrics.fmt_StoragePool(self.pool, self.instances, self.relations)
        self.assertEqual(result['sto_name'], 'SP-1')
        self.assertEqual(result['pdo_name'], 'PD-1')

    def test_none_name_falls_back_to_id(self):
        pool = dict(self.pool, name=None)
        result = siometrics.fmt_StoragePool(pool, self.instances, self.relations)
        self.assertEqual(result['sto_name'], 'sto-001')


class TestFmtSdc(unittest.TestCase):

    def test_named_sdc(self):
        sdc = {'id': 'sdc-001', 'name': 'my-host', 'sdcIp': '10.0.0.1', 'links': []}
        result = siometrics.fmt_Sdc(sdc, {}, {})
        self.assertEqual(result['sdc_name'], 'my-host')
        self.assertEqual(result['sdc_id'], 'sdc-001')

    def test_unnamed_sdc_falls_back_to_ip(self):
        sdc = {'id': 'sdc-001', 'name': None, 'sdcIp': '10.0.0.1', 'links': []}
        result = siometrics.fmt_Sdc(sdc, {}, {})
        self.assertEqual(result['sdc_name'], '10.0.0.1')

    def test_equals_in_name_escaped(self):
        sdc = {'id': 'sdc-001', 'name': 'host=A', 'sdcIp': '10.0.0.1', 'links': []}
        result = siometrics.fmt_Sdc(sdc, {}, {})
        self.assertIn('\\=', result['sdc_name'])


class TestFmtDeviceGroup(unittest.TestCase):

    def setUp(self):
        self.dg = {'id': 'dg-001', 'name': 'DG-SSD', 'mediaType': 'SSD', 'links': []}
        self.instances = {'ProtectionDomain': [PDO]}
        self.relations = make_relations('dg-001', 'DeviceGroup', 'pdo-001', 'ProtectionDomain')

    def test_returns_expected_keys(self):
        result = siometrics.fmt_DeviceGroup(self.dg, self.instances, self.relations)
        for key in ('dg_name', 'dg_id', 'dg_media_type', 'pdo_name', 'pdo_id'):
            self.assertIn(key, result)

    def test_media_type_ssd(self):
        result = siometrics.fmt_DeviceGroup(self.dg, self.instances, self.relations)
        self.assertEqual(result['dg_media_type'], 'SSD')

    def test_media_type_pmem(self):
        dg = dict(self.dg, mediaType='PMEM')
        result = siometrics.fmt_DeviceGroup(dg, self.instances, self.relations)
        self.assertEqual(result['dg_media_type'], 'PMEM')

    def test_parent_not_found_raises(self):
        bad_relations = {'children': {}, 'parents': {'dg-001': {'ProtectionDomain': ['no-such']}}}
        with self.assertRaises(Exception):
            siometrics.fmt_DeviceGroup(self.dg, self.instances, bad_relations)


class TestFmtSdt(unittest.TestCase):

    def setUp(self):
        self.sdt = {'id': 'sdt-001', 'name': 'sdt_ec-node-1', 'links': []}
        self.instances = {'ProtectionDomain': [PDO]}
        self.relations = make_relations('sdt-001', 'Sdt', 'pdo-001', 'ProtectionDomain')

    def test_returns_expected_keys(self):
        result = siometrics.fmt_Sdt(self.sdt, self.instances, self.relations)
        for key in ('sdt_name', 'sdt_id', 'pdo_name', 'pdo_id'):
            self.assertIn(key, result)

    def test_values(self):
        result = siometrics.fmt_Sdt(self.sdt, self.instances, self.relations)
        self.assertEqual(result['sdt_name'], 'sdt_ec-node-1')
        self.assertEqual(result['sdt_id'], 'sdt-001')
        self.assertEqual(result['pdo_name'], 'PD-1')
        self.assertEqual(result['pdo_id'], 'pdo-001')

    def test_none_name_falls_back_to_id(self):
        sdt = dict(self.sdt, name=None)
        result = siometrics.fmt_Sdt(sdt, self.instances, self.relations)
        self.assertEqual(result['sdt_name'], 'sdt-001')

    def test_parent_not_found_raises(self):
        bad_relations = {'children': {}, 'parents': {'sdt-001': {'ProtectionDomain': ['no-such']}}}
        with self.assertRaises(Exception):
            siometrics.fmt_Sdt(self.sdt, self.instances, bad_relations)


class TestFmtProtectionDomain(unittest.TestCase):

    def test_values(self):
        pdo = {'id': 'pdo-001', 'name': 'PD-1', 'links': []}
        result = siometrics.fmt_ProtectionDomain(pdo, {}, {})
        self.assertEqual(result['pdo_id'], 'pdo-001')
        self.assertEqual(result['pdo_name'], 'PD-1')

    def test_none_name_falls_back_to_id(self):
        pdo = {'id': 'pdo-001', 'name': None, 'links': []}
        result = siometrics.fmt_ProtectionDomain(pdo, {}, {})
        self.assertEqual(result['pdo_name'], 'pdo-001')


if __name__ == '__main__':
    unittest.main()
