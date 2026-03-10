# Copyright 2026 Dell Technologies
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

import argparse
import yaml
import os
import sio_sdk
import siometrics


def addMetrics(stype, fields, fmt):
    metrics = []
    for ftype,fvalue in fields.items():
        for fsubtype,fsubvalue in fvalue.items():
            suffix = '.'+ftype if ftype else ''
            suffix += '.'+fsubtype if fsubtype else ''
            metrics.append(  (siometrics.metric[stype]+suffix+','+siometrics.tags[stype]+' '+fsubvalue).format(**fmt) )
    return metrics

def stringifyFieldsV5(v5_stats, stype):
    fields = {}
    for v5_name, mapping in siometrics.v5_metrics.get(stype, {}).items():
        value = v5_stats.get(v5_name)
        if value is None:
            continue
        meas_suffix, field_name, rw = mapping
        if meas_suffix is not None:
            if meas_suffix not in fields:
                fields[meas_suffix] = {}
            if rw not in fields[meas_suffix]:
                fields[meas_suffix][rw] = ''
            if fields[meas_suffix][rw]:
                fields[meas_suffix][rw] += ','
            fields[meas_suffix][rw] += field_name + '=' + str(value)
        else:
            if '' not in fields:
                fields[''] = {'': ''}
            if fields['']['']:
                fields[''][''] += ','
            fields[''][''] += field_name + '=' + str(value)
    return fields

def printMetricsV5(instances, statistics, relations):
    base_fmt = {
        'clu_name': instances['System'][0]['name'] if 'name' in instances['System'][0] and instances['System'][0]['name'] is not None else instances['System'][0]['id'],
        'clu_id' : instances['System'][0]['id']
    }
    for stype in siometrics.v5_metrics.keys():
        if stype not in statistics: continue
        if stype not in siometrics.metric.keys(): continue
        if stype not in siometrics.tags.keys(): continue
        metrics = []
        for rid, v5_stats in statistics[stype].items():
            fmt = dict(base_fmt)
            try:
                if stype == 'System':
                    pass  # fmt already has cluster tags
                elif stype in siometrics.tags_funcs:
                    obj = None
                    for inst_obj in instances.get(stype, []):
                        if inst_obj['id'] == rid:
                            obj = inst_obj
                            break
                    if obj is None:
                        continue
                    fmt.update(siometrics.tags_funcs[stype](obj, instances, relations))
                else:
                    continue
                fields = stringifyFieldsV5(v5_stats, stype)
                if fields:
                    metrics.extend(addMetrics(stype, fields, fmt))
            except KeyError:
                continue
        for m in metrics:
            print(m)

def main(host, user, passw):
    try:
        sioclient = sio_sdk.SioRestClient(host, user, passw)
        (instances, relations) = sio_sdk.collect_instances(sioclient)
        statistics = sio_sdk.collect_statistics_v5(
            sioclient, siometrics.v5_metrics, siometrics.v5_resource_type)
        printMetricsV5(instances, statistics, relations)
    except sio_sdk.SioRestException as e:
        print(e.message)

if __name__ == "__main__":
    dname = os.path.dirname(os.path.abspath(__file__))
    with open(dname+'/clusters.yaml','r') as infile:
        clusters = yaml.load(infile, Loader=yaml.SafeLoader)
        infile.close()

    parser = argparse.ArgumentParser(description='ScaleIO CLI')
    parser.add_argument('cluster', help='choose a cluster', choices=sorted(clusters.keys()))
    args = parser.parse_args()

    main(clusters[args.cluster]['gateway'], clusters[args.cluster]['username'], clusters[args.cluster]['password'])
