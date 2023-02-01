import os
import sys
import json
import re
import requests

pattern = re.compile(r'(neu|bu)-(\d+)-(\d+)')
server_list = []

user = os.environ.get('HIL_USERNAME')
password = os.environ.get('HIL_PASSWORD')
url = os.environ.get('HIL_ENDPOINT') + '/v0/'
DEPLOY_KERNEL = os.environ.get('DEPLOY_KERNEL')
DEPLOY_RAMDISK = os.environ.get('DEPLOY_RAMDISK')
IPMI_USERNAME = os.environ.get('IPMI_USERNAME')
IPMI_PASSWORD = os.environ.get('IPMI_PASSWORD')

def show_node(node):
    api = 'node/' + node
    node_details = requests.get(url+api, auth=(user, password), verify=True)
    return json.loads(node_details.content)

def parse_node(node):

    coordinates = pattern.match(node['name'])

    # Figure out and set coordinates
    rack = coordinates.group(2)
    rackpos = coordinates.group(3)

    node_info = {}
    node_info['name'] = node['name']
    node_info['properties'] = { "capabilities": "iscsi_boot:True" }
    node_info['resource_class'] = "baremetal"
    node_info['driver'] = "ipmi"

    driver_info = {}

    driver_info['deploy_kernel'] = DEPLOY_KERNEL
    driver_info['deploy_ramdisk'] = DEPLOY_RAMDISK
    driver_info['ipmi_username'] = IPMI_USERNAME
    driver_info['ipmi_password'] = IPMI_PASSWORD
    driver_info['ipmi_address'] = f"10.0.{rack}.{rackpos}"

    node_info['driver_info'] = driver_info

    ports = []

    # Gather and set NIC information

    for nic in node['nics']:
        if nic['macaddr'] == 'nomacaddr':
            mac_addr = '00:00:00:00:00:00'
        else:
            mac_addr = nic['macaddr']

        if nic['switch'] == 'brocade_forty':
            switch_hostname = 'brocade-15-42'
            switchport = "FortyGigabitEthernet " + nic['port']
            switch_id = "50:eb:1a:61:5d:6a"
        elif nic['switch'] == 'brocade':
            switch_hostname = 'brocade-15-42'
            switchport = "TenGigabitEthernet " + nic['port']
            switch_id = "50:eb:1a:61:5d:6a"
        else:
            switch_hostname = nic['switch']
            switchport = nic['port']

        ports.append(
                    {'address': mac_addr,
                     'physical_network': 'datacentre',
                     'local_link_connection': {
                                    'switch_info': switch_hostname,
                                    'port_id': switchport,
                                    'switch_id': switch_id }
                        }
                     )

    node_info['ports'] = ports

    return node_info

def main():
    if len(sys.argv) <2 :
        sys.exit("please enter the name of one or more nodes")

    nodes = []

    for node in sys.argv[1:]:
        nodes.append(parse_node(show_node(node)))

    print(json.dumps({"nodes": nodes}))

if __name__ == "__main__":
    main()
