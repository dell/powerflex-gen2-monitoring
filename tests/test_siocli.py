"""
Unit tests for siocli.py — stringifyFieldsV5 and addMetrics.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import siometrics
import siocli


class TestStringifyFieldsV5(unittest.TestCase):

    def test_sub_measurement_rw(self):
        stats = {'host_read_iops': 100, 'host_write_iops': 200}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        self.assertIn('iops', fields)
        self.assertIn('read', fields['iops'])
        self.assertIn('write', fields['iops'])
        self.assertIn('host=100', fields['iops']['read'])
        self.assertIn('host=200', fields['iops']['write'])

    def test_multiple_fields_in_same_sub_measurement(self):
        stats = {'host_read_iops': 10, 'total_device_read_iops': 20}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        read_fields = fields['iops']['read']
        self.assertIn('host=10', read_fields)
        self.assertIn('device=20', read_fields)

    def test_scalar_in_base_measurement(self):
        stats = {'raw_total': 999999}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        self.assertIn('', fields)
        self.assertIn('', fields[''])
        self.assertIn('raw_total=999999', fields[''][''])

    def test_multiple_scalars_comma_separated(self):
        stats = {'raw_total': 100, 'raw_used': 50}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        base = fields['']['']
        self.assertIn('raw_total=100', base)
        self.assertIn('raw_used=50', base)
        self.assertIn(',', base)

    def test_none_value_skipped(self):
        stats = {'host_read_iops': None, 'host_write_iops': 42}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        self.assertNotIn('read', fields.get('iops', {}))
        self.assertIn('write', fields['iops'])

    def test_missing_metric_skipped(self):
        stats = {}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        self.assertEqual(fields, {})

    def test_unknown_stype_returns_empty(self):
        fields = siocli.stringifyFieldsV5({'host_read_iops': 1}, 'NonExistentType')
        self.assertEqual(fields, {})

    def test_directionless_rw_empty_string(self):
        stats = {'avg_controller_to_host_latency': 55, 'avg_host_to_controller_latency': 66}
        fields = siocli.stringifyFieldsV5(stats, 'Sdc')
        self.assertIn('latency', fields)
        self.assertIn('', fields['latency'])
        latency_base = fields['latency']['']
        self.assertIn('controller_to_host=55', latency_base)
        self.assertIn('host_to_controller=66', latency_base)

    def test_sdt_latency(self):
        stats = {'avg_controller_to_host_latency': 6, 'avg_host_to_controller_latency': 441}
        fields = siocli.stringifyFieldsV5(stats, 'Sdt')
        self.assertIn('latency', fields)
        self.assertIn('', fields['latency'])
        self.assertIn('controller_to_host=6', fields['latency'][''])
        self.assertIn('host_to_controller=441', fields['latency'][''])

    def test_trim_direction(self):
        stats = {'host_trim_iops': 77}
        fields = siocli.stringifyFieldsV5(stats, 'System')
        self.assertIn('iops', fields)
        self.assertIn('trim', fields['iops'])
        self.assertIn('host=77', fields['iops']['trim'])

    def test_bandwidth_with_rebalance_rebuild(self):
        stats = {'rebalance_rate': 1024, 'rebuild_rate': 2048}
        fields = siocli.stringifyFieldsV5(stats, 'ProtectionDomain')
        self.assertIn('bw', fields)
        self.assertIn('', fields['bw'])
        bw_base = fields['bw']['']
        self.assertIn('rebalance=1024', bw_base)
        self.assertIn('rebuild=2048', bw_base)

    def test_volume_scalars(self):
        stats = {'logical_used': 512, 'logical_provisioned': 1024}
        fields = siocli.stringifyFieldsV5(stats, 'Volume')
        self.assertIn('', fields)
        base = fields['']['']
        self.assertIn('logical_used=512', base)
        self.assertIn('logical_provisioned=1024', base)

    def test_all_v5_metric_tuples_are_3_element(self):
        for stype, metrics in siometrics.v5_metrics.items():
            for metric_name, mapping in metrics.items():
                self.assertEqual(len(mapping), 3,
                    f"{stype}.{metric_name} tuple should have 3 elements, got {len(mapping)}: {mapping}")

    def test_all_rw_values_are_valid(self):
        valid_rw = {'read', 'write', 'trim', ''}
        for stype, metrics in siometrics.v5_metrics.items():
            for metric_name, (_, _, rw) in metrics.items():
                self.assertIn(rw, valid_rw,
                    f"{stype}.{metric_name} has invalid rw='{rw}'")


class TestAddMetrics(unittest.TestCase):

    def _base_fmt(self):
        return {'clu_name': 'test-cluster', 'clu_id': 'abc123'}

    def test_sub_measurement_suffix(self):
        fields = {'iops': {'read': 'host=100,device=200'}}
        fmt = self._base_fmt()
        lines = siocli.addMetrics('System', fields, fmt)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('scaleio.cluster.iops.read,'))
        self.assertIn('host=100,device=200', lines[0])

    def test_base_measurement_no_suffix(self):
        fields = {'': {'': 'raw_total=999'}}
        fmt = self._base_fmt()
        lines = siocli.addMetrics('System', fields, fmt)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('scaleio.cluster,'))
        self.assertIn('raw_total=999', lines[0])

    def test_directionless_suffix(self):
        fields = {'latency': {'': 'controller_to_host=5,host_to_controller=10'}}
        fmt = self._base_fmt()
        lines = siocli.addMetrics('System', fields, fmt)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('scaleio.cluster.latency,'))
        self.assertIn('controller_to_host=5', lines[0])

    def test_tags_formatted_into_line(self):
        fields = {'iops': {'read': 'host=5'}}
        fmt = self._base_fmt()
        lines = siocli.addMetrics('System', fields, fmt)
        self.assertIn('cluster=test-cluster', lines[0])
        self.assertIn('cluster_id=abc123', lines[0])

    def test_multiple_sub_measurements_produce_multiple_lines(self):
        fields = {
            'iops': {'read': 'host=1', 'write': 'host=2'},
            'bw':   {'read': 'host=100'},
        }
        fmt = self._base_fmt()
        lines = siocli.addMetrics('System', fields, fmt)
        self.assertEqual(len(lines), 3)
        prefixes = [l.split(',')[0] for l in lines]
        self.assertIn('scaleio.cluster.iops.read', prefixes)
        self.assertIn('scaleio.cluster.iops.write', prefixes)
        self.assertIn('scaleio.cluster.bw.read', prefixes)

    def test_sdt_line_format(self):
        fields = {'latency': {'': 'controller_to_host=6,host_to_controller=441'}}
        fmt = {**self._base_fmt(),
               'sdt_name': 'sdt_ec-storage-node-4', 'sdt_id': 'ebdbcb8000000001',
               'pdo_id': '78e5b45200000000', 'pdo_name': 'PD-1'}
        lines = siocli.addMetrics('Sdt', fields, fmt)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('scaleio.sdt.latency,'))
        self.assertIn('sdt_name=sdt_ec-storage-node-4', lines[0])
        self.assertIn('controller_to_host=6', lines[0])


class TestMetricConsistency(unittest.TestCase):

    def test_all_v5_metric_types_have_tags(self):
        for stype in siometrics.v5_metrics:
            self.assertIn(stype, siometrics.tags,
                f"v5_metrics has '{stype}' but siometrics.tags does not")

    def test_all_v5_metric_types_have_metric(self):
        for stype in siometrics.v5_metrics:
            self.assertIn(stype, siometrics.metric,
                f"v5_metrics has '{stype}' but siometrics.metric does not")

    def test_all_v5_metric_types_have_v5_resource_type(self):
        for stype in siometrics.v5_metrics:
            self.assertIn(stype, siometrics.v5_resource_type,
                f"v5_metrics has '{stype}' but siometrics.v5_resource_type does not")

    def test_non_system_types_have_tags_func(self):
        for stype in siometrics.v5_metrics:
            if stype == 'System':
                continue
            self.assertIn(stype, siometrics.tags_funcs,
                f"v5_metrics has '{stype}' but siometrics.tags_funcs does not")

    def test_metric_names_are_lowercase_snake_case(self):
        import re
        snake = re.compile(r'^[a-z][a-z0-9_]*$')
        for stype, metrics in siometrics.v5_metrics.items():
            for metric_name in metrics:
                self.assertTrue(snake.match(metric_name),
                    f"{stype}.{metric_name}: metric key is not snake_case")

    def test_field_names_are_lowercase_snake_case(self):
        import re
        snake = re.compile(r'^[a-z][a-z0-9_]*$')
        for stype, metrics in siometrics.v5_metrics.items():
            for metric_name, (_, field_name, _) in metrics.items():
                if field_name:
                    self.assertTrue(snake.match(field_name),
                        f"{stype}.{metric_name}: field_name '{field_name}' is not snake_case")

    def test_v5_resource_type_values_are_lowercase(self):
        for stype, v5type in siometrics.v5_resource_type.items():
            self.assertEqual(v5type, v5type.lower(),
                f"v5_resource_type['{stype}'] = '{v5type}' is not lowercase")


if __name__ == '__main__':
    unittest.main()
