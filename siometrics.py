# Copyright 2026 Brian Dean
# 
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

################# FUNCTIONS #################

def fmt_StorageNode(node, instances, relations):
    parent = None
    for pdo in instances['ProtectionDomain']:
        if pdo['id'] in relations['parents'][node['id']]['ProtectionDomain']:
            parent = pdo
            break
    if parent is None:
        raise Exception('Parent not found')
    return { 'sn_name': node['name'].replace('=','\\='), 'sn_id': node['id'].replace('=','\\='),
             'pdo_name': parent['name'].replace('=','\\='), 'pdo_id': parent['id'].replace('=','\\=') }

def fmt_Device(device, instances, relations):
    parentSN = None
    parentPDO = None
    dev_parents = relations['parents'].get(device['id'], {})
    # v5 renamed Sds to StorageNode; check both
    sn_key = 'Sds' if 'Sds' in dev_parents else 'StorageNode'
    sn_instances = instances.get('Sds', []) or instances.get('StorageNode', [])
    for sn in sn_instances:
        if sn['id'] in dev_parents.get(sn_key, []):
            parentSN = sn
            break
    # v5: Device -> StorageNode -> ProtectionDomain (devices belong to DeviceGroups, not StoragePools)
    if parentSN is not None:
        sn_parents = relations['parents'].get(parentSN['id'], {})
        for pdo in instances['ProtectionDomain']:
            if pdo['id'] in sn_parents.get('ProtectionDomain', []):
                parentPDO = pdo
                break
    if parentSN is None or parentPDO is None:
        raise Exception('Parent not found')

    dev_id = device['id'].replace('=','\\=')
    dev_name = device['name'].replace('=','\\=') if device['name'] is not None else dev_id

    sn_id = parentSN['id'].replace('=','\\=')
    sn_name = parentSN['name'].replace('=','\\=') if parentSN['name'] is not None else sn_id

    pdo_id = parentPDO['id'].replace('=','\\=')
    pdo_name = parentPDO['name'].replace('=','\\=') if parentPDO['name'] is not None else pdo_id

    dev_path = device.get('deviceCurrentPathName', device['id']).replace('/dev/','',1).replace('=','\\=')

    return { 'dev_name': dev_name, 'dev_id': dev_id,
             'dev_path': dev_path,
             'sn_name': sn_name, 'sn_id': sn_id,
             'pdo_name': pdo_name, 'pdo_id': pdo_id }

def fmt_Volume(volume, instances, relations):
    parentSTO = None
    parentPDO = None
    for sto in instances['StoragePool']:
        if sto['id'] in relations['parents'][volume['id']]['StoragePool']:
            parentSTO = sto
            break
    for pdo in instances['ProtectionDomain']:
        if pdo['id'] in relations['parents'][parentSTO['id']]['ProtectionDomain']:
            parentPDO = pdo
            break
    if parentSTO is None or parentPDO is None:
        raise Exception('Parent not found')

    vol_id = volume['id'].replace('=','\\=')
    vol_name = volume['name'].replace('=','\\=') if volume['name'] is not None else vol_id

    sto_id = parentSTO['id'].replace('=','\\=')
    sto_name = parentSTO['name'].replace('=','\\=') if parentSTO['name'] is not None else sto_id

    pdo_id = parentPDO['id'].replace('=','\\=')
    pdo_name = parentPDO['name'].replace('=','\\=') if parentPDO['name'] is not None else pdo_id

    vol_type_map = {
        'ThinProvisioned': 'BaseVolume',
        'Snapshot': 'ThinClone',
    }
    raw_type = volume.get('volumeType', 'unknown')
    vol_type = vol_type_map.get(raw_type, raw_type).replace('=','\\=')

    return { 'vol_name': vol_name, 'vol_id': vol_id, 'vol_type': vol_type,
             'sto_name': sto_name, 'sto_id': sto_id,
             'pdo_name': pdo_name, 'pdo_id': pdo_id }

def fmt_StoragePool(pool, instances, relations):
    parent = None
    for pdo in instances['ProtectionDomain']:
        if pdo['id'] in relations['parents'][pool['id']]['ProtectionDomain']:
            parent = pdo
            break
    if parent is None:
        raise Exception('Parent not found')
    
    sto_id = pool['id'].replace('=','\\=')
    sto_name = pool['name'].replace('=','\\=') if pool['name'] is not None else sto_id

    pdo_id = parent['id'].replace('=','\\=')
    pdo_name = parent['name'].replace('=','\\=') if parent['name'] is not None else pdo_id

    return { 'sto_name': sto_name, 'sto_id': sto_id,
             'pdo_name': pdo_name, 'pdo_id': pdo_id }

def fmt_Sdc(sdc, instances, relations):
    name = sdc['name'] if sdc['name'] is not None else sdc['sdcIp']
    return { 'sdc_name': name.replace('=','\\='), 'sdc_id': sdc['id'].replace('=','\\=') }

def fmt_DeviceGroup(dg, instances, relations):
    parentPDO = None
    dg_parents = relations['parents'].get(dg['id'], {})
    for pdo in instances['ProtectionDomain']:
        if pdo['id'] in dg_parents.get('ProtectionDomain', []):
            parentPDO = pdo
            break
    if parentPDO is None:
        raise Exception('Parent not found')
    dg_id = dg['id'].replace('=','\\=')
    dg_name = dg['name'].replace('=','\\=') if dg['name'] is not None else dg_id
    media_type = dg.get('mediaType', 'unknown').replace('=','\\=')
    pdo_id = parentPDO['id'].replace('=','\\=')
    pdo_name = parentPDO['name'].replace('=','\\=') if parentPDO['name'] is not None else pdo_id
    return { 'dg_name': dg_name, 'dg_id': dg_id, 'dg_media_type': media_type,
             'pdo_name': pdo_name, 'pdo_id': pdo_id }

def fmt_Sdt(sdt, instances, relations):
    parentPDO = None
    sdt_parents = relations['parents'].get(sdt['id'], {})
    for pdo in instances['ProtectionDomain']:
        if pdo['id'] in sdt_parents.get('ProtectionDomain', []):
            parentPDO = pdo
            break
    if parentPDO is None:
        raise Exception('Parent not found')
    sdt_id = sdt['id'].replace('=','\\=')
    sdt_name = sdt['name'].replace('=','\\=') if sdt['name'] is not None else sdt_id
    pdo_id = parentPDO['id'].replace('=','\\=')
    pdo_name = parentPDO['name'].replace('=','\\=') if parentPDO['name'] is not None else pdo_id
    return { 'sdt_name': sdt_name, 'sdt_id': sdt_id,
             'pdo_name': pdo_name, 'pdo_id': pdo_id }

def fmt_ProtectionDomain(domain, instances, relations):
    pdo_id = domain['id']
    pdo_name = domain['name'].replace('=','\\=') if domain['name'] is not None else pdo_id

    return { 'pdo_name': pdo_name, 'pdo_id': pdo_id}

################# VARIABLES #################

tags = {
    'System'           : 'cluster={clu_name},cluster_id={clu_id}',
    'StorageNode'      : 'cluster={clu_name},cluster_id={clu_id},storage_node={sn_name},storage_node_id={sn_id},protection_domain_id={pdo_id},protection_domain_name={pdo_name}',
    'Device'           : 'cluster={clu_name},cluster_id={clu_id},storage_node={sn_name},storage_node_id={sn_id},device_name={dev_name},device_id={dev_id},device_path={dev_path},protection_domain_id={pdo_id},protection_domain_name={pdo_name}',
    'Volume'           : 'cluster={clu_name},cluster_id={clu_id},volume_name={vol_name},volume_id={vol_id},volume_type={vol_type},storage_pool_id={sto_id},storage_pool_name={sto_name},protection_domain_id={pdo_id},protection_domain_name={pdo_name}',
    'StoragePool'      : 'cluster={clu_name},cluster_id={clu_id},storage_pool_id={sto_id},storage_pool_name={sto_name},protection_domain_id={pdo_id},protection_domain_name={pdo_name}',
    'Sdc'              : 'cluster={clu_name},cluster_id={clu_id},sdc_name={sdc_name},sdc_id={sdc_id}',
    'DeviceGroup'      : 'cluster={clu_name},cluster_id={clu_id},device_group_name={dg_name},device_group_id={dg_id},media_type={dg_media_type},protection_domain_id={pdo_id},protection_domain_name={pdo_name}',
    'ProtectionDomain' : 'cluster={clu_name},cluster_id={clu_id},protection_domain_id={pdo_id},protection_domain_name={pdo_name}',
    'Sdt'              : 'cluster={clu_name},cluster_id={clu_id},sdt_name={sdt_name},sdt_id={sdt_id},protection_domain_id={pdo_id},protection_domain_name={pdo_name}'
}

metric = {
    'System'           : 'scaleio.cluster',
    'StorageNode'      : 'scaleio.storagenode',
    'Device'           : 'scaleio.device',
    'Volume'           : 'scaleio.volume',
    'StoragePool'      : 'scaleio.storagepool',
    'Sdc'              : 'scaleio.sdc',
    'DeviceGroup'      : 'scaleio.devicegroup',
    'ProtectionDomain' : 'scaleio.protectiondomain',
    'Sdt'              : 'scaleio.sdt'
}

tags_funcs = {
    'StorageNode'      : fmt_StorageNode,
    'Device'           : fmt_Device,
    'Volume'           : fmt_Volume,
    'StoragePool'      : fmt_StoragePool,
    'Sdc'              : fmt_Sdc,
    'DeviceGroup'      : fmt_DeviceGroup,
    'ProtectionDomain' : fmt_ProtectionDomain,
    'Sdt'              : fmt_Sdt
}

################# V5 API DEFINITIONS #################

# Maps type names to v5 resource_type strings
v5_resource_type = {
    'System'           : 'system',
    'StorageNode'      : 'storage_node',
    'Device'           : 'device',
    'Volume'           : 'volume',
    'StoragePool'      : 'storage_pool',
    'Sdc'              : 'sdc',
    'DeviceGroup'      : 'device_group',
    'ProtectionDomain' : 'protection_domain',
    'Sdt'              : 'sdt',
}

# Metrics to request from v5 API per resource type (old Gen1 type names as keys).
# Unified metric definitions per resource type.
# Each entry maps a v5 API metric name to a tuple: (measurement_suffix, field_name, rw)
#   - measurement_suffix: appended to base measurement name (e.g. 'iops' -> scaleio.cluster.iops.read)
#   - field_name: the InfluxDB field key
#   - rw: the final sub-key ('read', 'write', 'trim', or '' for directionless metrics)
# Scalars use (None, field_name, '') and land in the base measurement (e.g. scaleio.cluster).
v5_metrics = {
    # system: 74 verified metrics
    'System': {
        # IOPS
        'host_read_iops':                    ('iops', 'host', 'read'),
        'host_write_iops':                   ('iops', 'host', 'write'),
        'host_trim_iops':                    ('iops', 'host', 'trim'),
        'total_device_read_iops':            ('iops', 'device', 'read'),
        'total_device_write_iops':           ('iops', 'device', 'write'),
        'device_local_read_iops':            ('iops', 'device_local', 'read'),
        'device_local_write_iops':           ('iops', 'device_local', 'write'),
        'device_remote_read_iops':           ('iops', 'device_remote', 'read'),
        'device_remote_write_iops':          ('iops', 'device_remote', 'write'),
        'storage_fe_read_iops':              ('iops', 'storage_fe', 'read'),
        'storage_fe_write_iops':             ('iops', 'storage_fe', 'write'),
        'storage_fe_trim_iops':              ('iops', 'storage_fe', 'trim'),
        # Bandwidth (bytes/sec)
        'host_read_bandwidth':               ('bw', 'host', 'read'),
        'host_write_bandwidth':              ('bw', 'host', 'write'),
        'host_trim_bandwidth':               ('bw', 'host', 'trim'),
        'total_device_read_bandwidth':       ('bw', 'device', 'read'),
        'total_device_write_bandwidth':      ('bw', 'device', 'write'),
        'device_local_read_bandwidth':       ('bw', 'device_local', 'read'),
        'device_local_write_bandwidth':      ('bw', 'device_local', 'write'),
        'device_remote_read_bandwidth':      ('bw', 'device_remote', 'read'),
        'device_remote_write_bandwidth':     ('bw', 'device_remote', 'write'),
        'storage_fe_read_bandwidth':         ('bw', 'storage_fe', 'read'),
        'storage_fe_write_bandwidth':        ('bw', 'storage_fe', 'write'),
        'storage_fe_trim_bandwidth':         ('bw', 'storage_fe', 'trim'),
        # IO Size (bytes)
        'avg_fe_read_io_size':               ('iosize', 'host', 'read'),
        'avg_fe_write_io_size':              ('iosize', 'host', 'write'),
        'avg_fe_trim_io_size':               ('iosize', 'host', 'trim'),
        'avg_device_read_io_size':           ('iosize', 'device', 'read'),
        'avg_device_write_io_size':          ('iosize', 'device', 'write'),
        # Latency (µs)
        'avg_host_read_latency':             ('latency', 'host', 'read'),
        'avg_host_write_latency':            ('latency', 'host', 'write'),
        'avg_host_trim_latency':             ('latency', 'host', 'trim'),
        'avg_controller_to_host_latency':    ('latency', 'controller_to_host', ''),
        'avg_host_to_controller_latency':    ('latency', 'host_to_controller', ''),
        'avg_device_read_latency':           ('latency', 'device', 'read'),
        'avg_device_write_latency':          ('latency', 'device', 'write'),
        'storage_fe_read_latency':           ('latency', 'storage_fe', 'read'),
        'storage_fe_write_latency':          ('latency', 'storage_fe', 'write'),
        'storage_fe_trim_latency':           ('latency', 'storage_fe', 'trim'),
        # Capacity (bytes)
        'raw_total':                         (None, 'raw_total', ''),
        'raw_used':                          (None, 'raw_used', ''),
        'raw_free':                          (None, 'raw_free', ''),
        'raw_system':                        (None, 'raw_system', ''),
        'physical_total':                    (None, 'physical_total', ''),
        'physical_used':                     (None, 'physical_used', ''),
        'physical_free':                     (None, 'physical_free', ''),
        'physical_system':                   (None, 'physical_system', ''),
        'logical_used':                      (None, 'logical_used', ''),
        'logical_provisioned':               (None, 'logical_provisioned', ''),
        'logical_owned':                     (None, 'logical_owned', ''),
        'unreducible_data':                  (None, 'unreducible_data', ''),
        # Ratios
        'compression_ratio':                 (None, 'compression_ratio', ''),
        'data_reduction_ratio':              (None, 'data_reduction_ratio', ''),
        'efficiency_ratio':                  (None, 'efficiency_ratio', ''),
        'thin_provisioning_ratio':           (None, 'thin_provisioning_ratio', ''),
        'patterns_saving_ratio':             (None, 'patterns_saving_ratio', ''),
        'snapshot_saving_ratio':             (None, 'snapshot_saving_ratio', ''),
        'reducible_ratio':                   (None, 'reducible_ratio', ''),
    },
    # storage_node: 37 verified metrics
    'StorageNode': {
        # IOPS
        'total_device_read_iops':            ('iops', 'device', 'read'),
        'total_device_write_iops':           ('iops', 'device', 'write'),
        'device_local_read_iops':            ('iops', 'device_local', 'read'),
        'device_local_write_iops':           ('iops', 'device_local', 'write'),
        'device_remote_read_iops':           ('iops', 'device_remote', 'read'),
        'device_remote_write_iops':          ('iops', 'device_remote', 'write'),
        'storage_fe_read_iops':              ('iops', 'storage_fe', 'read'),
        'storage_fe_write_iops':             ('iops', 'storage_fe', 'write'),
        'storage_fe_trim_iops':              ('iops', 'storage_fe', 'trim'),
        # Bandwidth (bytes/sec)
        'total_device_read_bandwidth':       ('bw', 'device', 'read'),
        'total_device_write_bandwidth':      ('bw', 'device', 'write'),
        'device_local_read_bandwidth':       ('bw', 'device_local', 'read'),
        'device_local_write_bandwidth':      ('bw', 'device_local', 'write'),
        'device_remote_read_bandwidth':      ('bw', 'device_remote', 'read'),
        'device_remote_write_bandwidth':     ('bw', 'device_remote', 'write'),
        'storage_fe_read_bandwidth':         ('bw', 'storage_fe', 'read'),
        'storage_fe_write_bandwidth':        ('bw', 'storage_fe', 'write'),
        'storage_fe_trim_bandwidth':         ('bw', 'storage_fe', 'trim'),
        # IO Size (bytes)
        'avg_fe_read_io_size':               ('iosize', 'host', 'read'),
        'avg_fe_write_io_size':              ('iosize', 'host', 'write'),
        'avg_fe_trim_io_size':               ('iosize', 'host', 'trim'),
        'avg_device_read_io_size':           ('iosize', 'device', 'read'),
        'avg_device_write_io_size':          ('iosize', 'device', 'write'),
        # Latency (µs)
        'avg_device_read_latency':           ('latency', 'device', 'read'),
        'avg_device_write_latency':          ('latency', 'device', 'write'),
        'storage_fe_read_latency':           ('latency', 'storage_fe', 'read'),
        'storage_fe_write_latency':          ('latency', 'storage_fe', 'write'),
        'storage_fe_trim_latency':           ('latency', 'storage_fe', 'trim'),
        # Capacity (bytes)
        'raw_total':                         (None, 'raw_total', ''),
    },
    # sdc: 11 verified metrics
    'Sdc': {
        # IOPS
        'host_read_iops':                    ('iops', 'host', 'read'),
        'host_write_iops':                   ('iops', 'host', 'write'),
        'host_trim_iops':                    ('iops', 'host', 'trim'),
        # Bandwidth (bytes/sec)
        'host_read_bandwidth':               ('bw', 'host', 'read'),
        'host_write_bandwidth':              ('bw', 'host', 'write'),
        'host_trim_bandwidth':               ('bw', 'host', 'trim'),
        # Latency (µs)
        'avg_host_read_latency':             ('latency', 'host', 'read'),
        'avg_host_write_latency':            ('latency', 'host', 'write'),
        'avg_host_trim_latency':             ('latency', 'host', 'trim'),
        'avg_controller_to_host_latency':    ('latency', 'controller_to_host', ''),
        'avg_host_to_controller_latency':    ('latency', 'host_to_controller', ''),
    },
    # volume: 12 verified metrics
    'Volume': {
        # IOPS
        'host_read_iops':                    ('iops', 'host', 'read'),
        'host_write_iops':                   ('iops', 'host', 'write'),
        'host_trim_iops':                    ('iops', 'host', 'trim'),
        # Bandwidth (bytes/sec)
        'host_read_bandwidth':               ('bw', 'host', 'read'),
        'host_write_bandwidth':              ('bw', 'host', 'write'),
        'host_trim_bandwidth':               ('bw', 'host', 'trim'),
        # Latency (µs)
        'avg_host_read_latency':             ('latency', 'host', 'read'),
        'avg_host_write_latency':            ('latency', 'host', 'write'),
        'avg_host_trim_latency':             ('latency', 'host', 'trim'),
        # Capacity (bytes)
        'logical_used':                      (None, 'logical_used', ''),
        'logical_provisioned':               (None, 'logical_provisioned', ''),
    },
    # storage_pool: 48 verified metrics
    'StoragePool': {
        # IOPS
        'host_read_iops':                    ('iops', 'host', 'read'),
        'host_write_iops':                   ('iops', 'host', 'write'),
        'host_trim_iops':                    ('iops', 'host', 'trim'),
        'storage_fe_read_iops':              ('iops', 'storage_fe', 'read'),
        'storage_fe_write_iops':             ('iops', 'storage_fe', 'write'),
        'storage_fe_trim_iops':              ('iops', 'storage_fe', 'trim'),
        # Bandwidth (bytes/sec)
        'host_read_bandwidth':               ('bw', 'host', 'read'),
        'host_write_bandwidth':              ('bw', 'host', 'write'),
        'host_trim_bandwidth':               ('bw', 'host', 'trim'),
        'storage_fe_read_bandwidth':         ('bw', 'storage_fe', 'read'),
        'storage_fe_write_bandwidth':        ('bw', 'storage_fe', 'write'),
        'storage_fe_trim_bandwidth':         ('bw', 'storage_fe', 'trim'),
        # IO Size (bytes)
        'avg_fe_read_io_size':               ('iosize', 'host', 'read'),
        'avg_fe_write_io_size':              ('iosize', 'host', 'write'),
        'avg_fe_trim_io_size':               ('iosize', 'host', 'trim'),
        # Latency (µs)
        'avg_host_read_latency':             ('latency', 'host', 'read'),
        'avg_host_write_latency':            ('latency', 'host', 'write'),
        'avg_host_trim_latency':             ('latency', 'host', 'trim'),
        'storage_fe_read_latency':           ('latency', 'storage_fe', 'read'),
        'storage_fe_write_latency':          ('latency', 'storage_fe', 'write'),
        'storage_fe_trim_latency':           ('latency', 'storage_fe', 'trim'),
        # Capacity (bytes)
        'raw_used':                          (None, 'raw_used', ''),
        'physical_free':                     (None, 'physical_free', ''),
        'physical_total':                    (None, 'physical_total', ''),
        'physical_used':                     (None, 'physical_used', ''),
        'physical_system':                   (None, 'physical_system', ''),
        'logical_used':                      (None, 'logical_used', ''),
        'logical_provisioned':               (None, 'logical_provisioned', ''),
        'logical_owned':                     (None, 'logical_owned', ''),
        'over_provisioning_limit':           (None, 'over_provisioning_limit', ''),
        'unreducible_data':                  (None, 'unreducible_data', ''),
        # Ratios
        'compression_ratio':                 (None, 'compression_ratio', ''),
        'data_reduction_ratio':              (None, 'data_reduction_ratio', ''),
        'efficiency_ratio':                  (None, 'efficiency_ratio', ''),
        'thin_provisioning_ratio':           (None, 'thin_provisioning_ratio', ''),
        'patterns_saving_ratio':             (None, 'patterns_saving_ratio', ''),
        'snapshot_saving_ratio':             (None, 'snapshot_saving_ratio', ''),
        'reducible_ratio':                   (None, 'reducible_ratio', ''),
        'utilization_ratio':                 (None, 'utilization_ratio', ''),
    },
    # device: 26 verified metrics
    'Device': {
        # IOPS
        'total_device_read_iops':            ('iops', 'device', 'read'),
        'total_device_write_iops':           ('iops', 'device', 'write'),
        'device_local_read_iops':            ('iops', 'device_local', 'read'),
        'device_local_write_iops':           ('iops', 'device_local', 'write'),
        'device_remote_read_iops':           ('iops', 'device_remote', 'read'),
        'device_remote_write_iops':          ('iops', 'device_remote', 'write'),
        # Bandwidth (bytes/sec)
        'total_device_read_bandwidth':       ('bw', 'device', 'read'),
        'total_device_write_bandwidth':      ('bw', 'device', 'write'),
        'device_local_read_bandwidth':       ('bw', 'device_local', 'read'),
        'device_local_write_bandwidth':      ('bw', 'device_local', 'write'),
        'device_remote_read_bandwidth':      ('bw', 'device_remote', 'read'),
        'device_remote_write_bandwidth':     ('bw', 'device_remote', 'write'),
        # IO Size (bytes)
        'avg_device_read_io_size':           ('iosize', 'device', 'read'),
        'avg_device_write_io_size':          ('iosize', 'device', 'write'),
        # Latency (µs)
        'avg_device_read_latency':           ('latency', 'device', 'read'),
        'avg_device_write_latency':          ('latency', 'device', 'write'),
        # Capacity (bytes)
        'raw_total':                         (None, 'raw_total', ''),
    },
    # protection_domain: 79 verified metrics
    'ProtectionDomain': {
        # IOPS
        'host_read_iops':                    ('iops', 'host', 'read'),
        'host_write_iops':                   ('iops', 'host', 'write'),
        'host_trim_iops':                    ('iops', 'host', 'trim'),
        'total_device_read_iops':            ('iops', 'device', 'read'),
        'total_device_write_iops':           ('iops', 'device', 'write'),
        'storage_fe_read_iops':              ('iops', 'storage_fe', 'read'),
        'storage_fe_write_iops':             ('iops', 'storage_fe', 'write'),
        'storage_fe_trim_iops':              ('iops', 'storage_fe', 'trim'),
        # Bandwidth (bytes/sec)
        'host_read_bandwidth':               ('bw', 'host', 'read'),
        'host_write_bandwidth':              ('bw', 'host', 'write'),
        'host_trim_bandwidth':               ('bw', 'host', 'trim'),
        'total_device_read_bandwidth':       ('bw', 'device', 'read'),
        'total_device_write_bandwidth':      ('bw', 'device', 'write'),
        'rebalance_rate':                    ('bw', 'rebalance', ''),
        'rebuild_rate':                      ('bw', 'rebuild', ''),
        'storage_fe_read_bandwidth':         ('bw', 'storage_fe', 'read'),
        'storage_fe_write_bandwidth':        ('bw', 'storage_fe', 'write'),
        'storage_fe_trim_bandwidth':         ('bw', 'storage_fe', 'trim'),
        # IO Size (bytes)
        'avg_fe_read_io_size':               ('iosize', 'host', 'read'),
        'avg_fe_write_io_size':              ('iosize', 'host', 'write'),
        'avg_fe_trim_io_size':               ('iosize', 'host', 'trim'),
        'avg_device_read_io_size':           ('iosize', 'device', 'read'),
        'avg_device_write_io_size':          ('iosize', 'device', 'write'),
        # Latency (µs)
        'avg_host_read_latency':             ('latency', 'host', 'read'),
        'avg_host_write_latency':            ('latency', 'host', 'write'),
        'avg_host_trim_latency':             ('latency', 'host', 'trim'),
        'avg_device_read_latency':           ('latency', 'device', 'read'),
        'avg_device_write_latency':          ('latency', 'device', 'write'),
        'storage_fe_read_latency':           ('latency', 'storage_fe', 'read'),
        'storage_fe_write_latency':          ('latency', 'storage_fe', 'write'),
        'storage_fe_trim_latency':           ('latency', 'storage_fe', 'trim'),
        # Capacity (bytes)
        'raw_total':                         (None, 'raw_total', ''),
        'raw_used':                          (None, 'raw_used', ''),
        'raw_free':                          (None, 'raw_free', ''),
        'raw_spare':                         (None, 'raw_spare', ''),
        'raw_system':                        (None, 'raw_system', ''),
        'raw_spare_used':                    (None, 'raw_spare_used', ''),
        'physical_total':                    (None, 'physical_total', ''),
        'physical_used':                     (None, 'physical_used', ''),
        'physical_free':                     (None, 'physical_free', ''),
        'physical_system':                   (None, 'physical_system', ''),
        'logical_used':                      (None, 'logical_used', ''),
        'logical_provisioned':               (None, 'logical_provisioned', ''),
        'logical_owned':                     (None, 'logical_owned', ''),
        'unreducible_data':                  (None, 'unreducible_data', ''),
        # Ratios
        'compression_ratio':                 (None, 'compression_ratio', ''),
        'data_reduction_ratio':              (None, 'data_reduction_ratio', ''),
        'efficiency_ratio':                  (None, 'efficiency_ratio', ''),
        'thin_provisioning_ratio':           (None, 'thin_provisioning_ratio', ''),
        'patterns_saving_ratio':             (None, 'patterns_saving_ratio', ''),
        'snapshot_saving_ratio':             (None, 'snapshot_saving_ratio', ''),
        'reducible_ratio':                   (None, 'reducible_ratio', ''),
    },
    # device_group: 69 verified metrics (covers both SSD/storage and PMEM/WRC types)
    'DeviceGroup': {
        # IOPS
        'host_read_iops':                    ('iops', 'host', 'read'),
        'host_write_iops':                   ('iops', 'host', 'write'),
        'host_trim_iops':                    ('iops', 'host', 'trim'),
        'total_device_read_iops':            ('iops', 'device', 'read'),
        'total_device_write_iops':           ('iops', 'device', 'write'),
        'device_local_read_iops':            ('iops', 'device_local', 'read'),
        'device_local_write_iops':           ('iops', 'device_local', 'write'),
        'device_remote_read_iops':           ('iops', 'device_remote', 'read'),
        'device_remote_write_iops':          ('iops', 'device_remote', 'write'),
        'storage_fe_read_iops':              ('iops', 'storage_fe', 'read'),
        'storage_fe_write_iops':             ('iops', 'storage_fe', 'write'),
        'storage_fe_trim_iops':              ('iops', 'storage_fe', 'trim'),
        'total_device_pmem_read_iops':       ('iops', 'device_pmem', 'read'),
        'total_device_pmem_write_iops':      ('iops', 'device_pmem', 'write'),
        'total_wrc_read_iops':               ('iops', 'wrc', 'read'),
        'total_wrc_write_iops':              ('iops', 'wrc', 'write'),
        # Bandwidth (bytes/sec)
        'host_read_bandwidth':               ('bw', 'host', 'read'),
        'host_write_bandwidth':              ('bw', 'host', 'write'),
        'host_trim_bandwidth':               ('bw', 'host', 'trim'),
        'total_device_read_bandwidth':       ('bw', 'device', 'read'),
        'total_device_write_bandwidth':      ('bw', 'device', 'write'),
        'device_local_read_bandwidth':       ('bw', 'device_local', 'read'),
        'device_local_write_bandwidth':      ('bw', 'device_local', 'write'),
        'device_remote_read_bandwidth':      ('bw', 'device_remote', 'read'),
        'device_remote_write_bandwidth':     ('bw', 'device_remote', 'write'),
        'storage_fe_read_bandwidth':         ('bw', 'storage_fe', 'read'),
        'storage_fe_write_bandwidth':        ('bw', 'storage_fe', 'write'),
        'storage_fe_trim_bandwidth':         ('bw', 'storage_fe', 'trim'),
        'total_device_pmem_read_bandwidth':  ('bw', 'device_pmem', 'read'),
        'total_device_pmem_write_bandwidth': ('bw', 'device_pmem', 'write'),
        'total_wrc_read_bandwidth':          ('bw', 'wrc', 'read'),
        'total_wrc_write_bandwidth':         ('bw', 'wrc', 'write'),
        'rebalance_rate':                    ('bw', 'rebalance', ''),
        'rebuild_rate':                      ('bw', 'rebuild', ''),
        # IO Size (bytes)
        'avg_fe_read_io_size':               ('iosize', 'host', 'read'),
        'avg_fe_write_io_size':              ('iosize', 'host', 'write'),
        'avg_fe_trim_io_size':               ('iosize', 'host', 'trim'),
        'avg_device_read_io_size':           ('iosize', 'device', 'read'),
        'avg_device_write_io_size':          ('iosize', 'device', 'write'),
        'avg_device_pmem_read_io_size':      ('iosize', 'device_pmem', 'read'),
        'avg_device_pmem_write_io_size':     ('iosize', 'device_pmem', 'write'),
        'avg_wrc_read_io_size':              ('iosize', 'wrc', 'read'),
        'avg_wrc_write_io_size':             ('iosize', 'wrc', 'write'),
        # Latency (µs)
        'avg_host_read_latency':             ('latency', 'host', 'read'),
        'avg_host_write_latency':            ('latency', 'host', 'write'),
        'avg_host_trim_latency':             ('latency', 'host', 'trim'),
        'avg_device_read_latency':           ('latency', 'device', 'read'),
        'avg_device_write_latency':          ('latency', 'device', 'write'),
        'avg_device_pmem_read_latency':      ('latency', 'device_pmem', 'read'),
        'avg_device_pmem_write_latency':     ('latency', 'device_pmem', 'write'),
        'avg_wrc_read_latency':              ('latency', 'wrc', 'read'),
        'avg_wrc_write_latency':             ('latency', 'wrc', 'write'),
        'storage_fe_read_latency':           ('latency', 'storage_fe', 'read'),
        'storage_fe_write_latency':          ('latency', 'storage_fe', 'write'),
        'storage_fe_trim_latency':           ('latency', 'storage_fe', 'trim'),
        # Capacity (bytes)
        'raw_total':                         (None, 'raw_total', ''),
        'raw_used':                          (None, 'raw_used', ''),
        'raw_free':                          (None, 'raw_free', ''),
        'raw_spare':                         (None, 'raw_spare', ''),
        'raw_system':                        (None, 'raw_system', ''),
        'raw_spare_used':                    (None, 'raw_spare_used', ''),
        'raw_rebuild':                       (None, 'raw_rebuild', ''),
        'raw_health_degraded':               (None, 'raw_health_degraded', ''),
        'raw_health_degraded_critical':      (None, 'raw_health_degraded_critical', ''),
        'raw_health_failed':                 (None, 'raw_health_failed', ''),
        'physical_total':                    (None, 'physical_total', ''),
        'physical_used':                     (None, 'physical_used', ''),
        'physical_free':                     (None, 'physical_free', ''),
        'physical_system':                   (None, 'physical_system', ''),
    },
    # sdt: 2 verified metrics (NVMe/TCP target)
    'Sdt': {
        # Latency (µs) — directionless path latency
        'avg_controller_to_host_latency':    ('latency', 'controller_to_host', ''),
        'avg_host_to_controller_latency':    ('latency', 'host_to_controller', ''),
    },
}
