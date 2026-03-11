# Copyright 2026 Dell, Inc.
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

import sys
import json
import time
from sio_sdk.SioSdk import SioRestClient
from sio_sdk.SioSdk import SioRestException
from sio_sdk.SioSdk import err

def collect_instances(sio_rest_client):
    instances = {}
    relations = {'children':{}, 'parents':{}}
    alldata = sio_rest_client.get_json('/api/instances')
    for siotype, sioobjs in alldata.items():
        if siotype == 'System' or siotype.endswith('List'):
            sio_type = siotype[0].upper()+siotype[1:].replace('List','')
            instances[sio_type] = []
            if sioobjs:
                if siotype == 'System':
                    instances[sio_type].append(sioobjs)
                else:
                    instances[sio_type].extend(sioobjs)
                for sio_obj in instances[sio_type]:
                    for sio_obj_link in sio_obj['links']:
                        if  sio_obj_link['rel'].startswith('/api/parent'):
                            link_type = sio_obj_link['href'].split(':')[0].split('/')[-1]
                            link_id = sio_obj_link['href'].split(':')[-1]
                            if link_id not in relations['children']:
                                relations['children'][link_id] = {}
                            if sio_type not in relations['children'][link_id]:
                                relations['children'][link_id][sio_type] = []
                            if sio_obj['id'] not in relations['parents']:
                                relations['parents'][sio_obj['id']] = {}
                            if link_type not in relations['parents'][sio_obj['id']]:
                                relations['parents'][sio_obj['id']][link_type] = []
                            relations['children'][link_id][sio_type].append(sio_obj['id'])
                            relations['parents'][sio_obj['id']][link_type].append(link_id)
    return (instances, relations)

def collect_statistics_v5(sio_rest_client, v5_metrics_config, v5_resource_type_map):
    """
        Query the v5 /dtapi/rest/v1/metrics/query endpoint for each resource type.
        Omits 'ids' to get all instances.

        Returns dict keyed by type name (e.g. 'System', 'StorageNode'):
          {
            'System':      { '<id>': { 'metric_name': value, ... } }
            'StorageNode': { '<id>': { 'metric_name': value, ... }, ... }
            ...
          }
    """
    statistics = {}
    for old_type, metrics_def in v5_metrics_config.items():
        v5_type = v5_resource_type_map.get(old_type)
        if not v5_type:
            continue

        all_metrics = list(metrics_def.keys())
        if not all_metrics:
            continue

        body = {
            'resource_type': v5_type,
            'metrics': all_metrics,
        }

        try:
            response = sio_rest_client.post_json('/dtapi/rest/v1/metrics/query', body)
        except SioRestException as e:
            err("v5 metrics query failed for {0}: {1}".format(old_type, e))
            continue

        resources = response.get('resources', [])
        type_stats = {}
        for resource in resources:
            rid = resource['id']
            metric_values = {}
            for m in resource.get('metrics', []):
                vals = m.get('values', [])
                metric_values[m['name']] = vals[0] if vals else None
            type_stats[rid] = metric_values

        if old_type == 'System' and type_stats:
            # System has one instance; store its metrics directly (keyed by id for consistency)
            statistics[old_type] = type_stats
        else:
            statistics[old_type] = type_stats

    return statistics

def st_time(func):
    """
        Function decorator to calculate duration
    """
    def st_func(*args, **keyArgs):
        """
            Execute decorated function between two time collection.
        """
        stime = time.time()
        result = func(*args, **keyArgs)
        err("Function=%s, Time=%s" % (func.__name__, time.time() - stime))
        return result
    return st_func
