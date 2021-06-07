#!/usr/bin/python3
# encoding:utf-8

from elasticsearch import Elasticsearch
from pyzabbix import ZabbixAPI
import sys
import os
import subprocess
from re import compile, IGNORECASE

def login(ZABBIX_SERVER, USER, PASSWORD):
    zapi = ZabbixAPI(ZABBIX_SERVER)
    zapi.login(USER, PASSWORD)
    return zapi

def gethostid(auth, HOSTNAME):
    request = ZabbixAPI.do_request(auth, 'host.get', params={"filter": {"host": HOSTNAME}})
    if request['result']:
        return request['result'][0]['hostid']
    else:
        print("找不到该主机")
        sys.exit(1)

def getapplicationid(auth, hostid):
        request = ZabbixAPI.do_request(auth, 'application.get', params={"name": "elasticsearch_cluster", "hostid": hostid})
        if request['result']:
            return request['result']
        else:
            print("找不到该主机")
            return request['result']

def create_item(auth, URL, hostid, applicationid):
    request = ZabbixAPI.do_request(auth, 'httptest.get', params={"filter": {"name": URL}})
    if request['result']:
        print('该web监控已经添加过了')
    else:
        try:
            ZabbixAPI.do_request(auth, 'httptest.create',
                                 params={"name": URL, "hostid": hostid, "applicationid": applicationid,
                                         "delay": '60', "retries": '3',
                                         "steps": [{'name': URL, 'url': URL, 'no': '1'}]})
        except Exception as e:
            print(e)

def create_trigger(auth, HOSTNAME, URL):
    expression = "{" + "{0}:web.test.fail[{1}].last()".format(HOSTNAME, URL) + "}" + "<>0"
    try:
        ZabbixAPI.do_request(auth, 'trigger.create', params={
            "description": "从监控机（172.18.11.34）访问{0}出现问题,如果网络和主机性能没问题，并且是单节点报错请尝试重启对应的tomcat".format(URL),
            "expression": expression, "priority": 5})
    except Exception as e:
        print(e)



if '__main__' == __name__:
    es = Elasticsearch(
        ['http://10.0.5.111:9201'],
        http_auth=('elastic', 'icmori-sz@IDC.2019'),
        sniff_on_connection_fail=True,
        sniffer_timeout=60
    )

    # 获取elasticsearch集群状态
    cluster_info = es.cluster.health()
    cluster_name = cluster_info['cluster_name']
    status = cluster_info['status']
    timed_out = cluster_info['timed_out']
    number_of_nodes = cluster_info['number_of_nodes']
    number_of_data_nodes = cluster_info['number_of_data_nodes']
    active_primary_shards = cluster_info['active_primary_shards']
    active_shards = cluster_info['active_shards']
    relocating_shards = cluster_info['relocating_shards']
    initializing_shards = cluster_info['initializing_shards']
    unassigned_shards = cluster_info['unassigned_shards']
    delayed_unassigned_shards = cluster_info['delayed_unassigned_shards']
    number_of_pending_tasks = cluster_info['number_of_pending_tasks']
    number_of_in_flight_fetch = cluster_info['number_of_in_flight_fetch']
    task_max_waiting_in_queue_millis = cluster_info['task_max_waiting_in_queue_millis']
    active_shards_percent_as_number = cluster_info['active_shards_percent_as_number']

    ZABBIX_SERVER = 'http://monitor.icmori.com/zabbix/'
    USER = "Admin"
    PASSWORD = "password"
    HOSTNAME = "elasticsearch_cluster_info"

    #zbx_auth = login(ZABBIX_SERVER, USER, PASSWORD)
    #hostid = gethostid(zbx_auth, HOSTNAME)
    #print(hostid)
    #applicationid = getapplicationid(zbx_auth, hostid)

    for key in cluster_info:
        ZABBIX_SENDER = "zabbix_sender -s {} -z 10.0.5.21 -k {} -o {}".format(HOSTNAME, key, cluster_info[key])
        print(ZABBIX_SENDER)
        subprocess.Popen(ZABBIX_SENDER, shell=True, stdout=subprocess.PIPE)