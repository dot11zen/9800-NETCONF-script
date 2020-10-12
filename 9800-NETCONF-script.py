#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 9800-NETCONF-script.py:
    * Get NETCONF capabilities of the Cisco 9800 wireless controller
    * Import YANG schemas
    * Export the static AP tags configuration for Access Points on Cisco 9800
    * Edit the AP tags configuration
"""

# Import ncclient module for Netconf
from ncclient import manager, xml_
import xml.dom.minidom
import xmltodict
import pprint
import json
import re
import csv
import time
import os
from datetime import datetime
from collections import OrderedDict

# Get NETCONF capabilities
def get_capabilities(m):

    print("Printing server capabilities:")

    capabilities = []
    for capability in m.server_capabilities:
        print("\t{}".format(capability))
        capabilities.append(capability)
    print("\n", end = "")

    return capabilities

# Get the YANG schema and write them to text files
def get_schemas(m, capabilities):

    # Scan the capabilities and extract modules using regular expression
    print("Extracting YANG module names:")

    modules = []
    for capability in capabilities:
        supported_model = re.search("module=([a-zA-Z0-9_.-]*)", capability)
        if supported_model is not None:
            print("\t{}".format(supported_model.groups(0)[0]))
            modules.append(supported_model.groups(0)[0])
    print("\n", end = "")

    # Create subdirectory if not exits
    if not os.path.exists("YANG_schemas"):
        os.makedirs("YANG_schemas")

    # For each module, import the schema into text files
    print("Importing YANG schemas from NETCONF server...")
    for model in modules:
        schema = m.get_schema(model)
        # Open new file handle.
        with open("YANG_schemas/{}".format(model), "w") as f:
            f.write(schema.data)
    print("Importing YANG schemas from NETCONF server finished\n")

    return modules

# Get the full running configuration
def get_full_config(m):

    # Execute NETCONF get-config() to retrieve all the configuration data
    print("Importing NETCONF full configuration. This may take a while...")
    result = m.get_config(source="running")

    # Parse the XML file
    xml_doc = xml.dom.minidom.parseString(result.xml)

    # Print all the configuration
    print("NETCONF full configuration using get-config() method:\n{}".format(xml_doc.toprettyxml()))

# Get the AP tag configuration
def get_tags_config(m):

    # Create an XML filter
    filter = """
    <filter>
        <ap-cfg-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-ap-cfg">
            <ap-tags>
                <ap-tag></ap-tag>
            </ap-tags>
        </ap-cfg-data>
    </filter>
    """

    # Execute the NETCONF get() to retrieve all the AP tag configuration data
    result = m.get(filter)

    # Parse the XML file
    xml_doc = xml.dom.minidom.parseString(result.xml)

    # Print the configuration
    print("NETCONF AP tag configuration using get() method and XML filter:\n{}\n".format(xml_doc.toprettyxml()))

    # Create a list of AP tag configuration
    netconf_data = xmltodict.parse(result.xml)["rpc-reply"]["data"]
    if netconf_data == None:
        # No AP configuration has been returned
        ap_list = []
    elif isinstance(netconf_data["ap-cfg-data"]["ap-tags"]["ap-tag"], OrderedDict):
        # Only one AP configuration has been returned with a type of OrderedDict. Wrapping it into a list
        ap_list = [netconf_data["ap-cfg-data"]["ap-tags"]["ap-tag"]]
    else:
        # Multiple AP configurations have been returned
        ap_list = netconf_data["ap-cfg-data"]["ap-tags"]["ap-tag"]

    return ap_list

# Create a CSV file with the AP tag configuration
def csv_write(ap_list):

    # Get the current date and time
    today = datetime.today()

    # Create a Comma Separated Value file with the AP tag configuration
    with open("ap-tags-config-{}.csv".format(today.strftime("%Y-%m-%d-%H-%M-%S")), mode="w", newline="") as csv_file:

        csv_writer = csv.writer(csv_file, delimiter=",", quotechar="'", quoting=csv.QUOTE_MINIMAL)

        print("Writing AP tag configuration to CSV file named {}:".format(csv_file.name))

        for ap in ap_list:
            # Print the AP tag configuration
            print("\tAP MAC:{}, policy-tag:{}, site-tag:{}, rf-tag:{}".format(ap["ap-mac"],
               ap["policy-tag"] if "policy-tag" in ap else "",
               ap["site-tag"] if "site-tag" in ap else "",
               ap["rf-tag"] if "rf-tag" in ap else ""))

            # Write the AP tag configuration as a row in the CSV file
            csv_writer.writerow([ap["ap-mac"],
                                 ap["policy-tag"] if "policy-tag" in ap else "",
                                 ap["site-tag"] if "site-tag" in ap else "",
                                 ap["rf-tag"] if "rf-tag" in ap else ""])

        print("\n", end = "")

# Edit the AP tag configuration
def edit_config_one_AP(m):

    # Create a NETCONF template
    netconf_template = """
    <config>
        <ap-cfg-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-ap-cfg">
            <ap-tags>
                <ap-tag>
                    <ap-mac>11:22:33:44:55:66</ap-mac>
                    <site-tag>Sydney</site-tag>
                </ap-tag>
            </ap-tags>
        </ap-cfg-data>
    </config>
    """

    # Execute NETCONF edit_config() to edit the AP tag configuration
    result = m.edit_config(netconf_template, target = "running")

    # Parse the XML file
    xml_doc = xml.dom.minidom.parseString(result.xml)

    # Print the configuration
    print("NETCONF response for editing the AP tag configuration:\n{}".format(xml_doc.toprettyxml()))

# Edit the AP tag configuration
def edit_config(m):

    ap_tags = ""

    # Import the AP tag configuration from the "ap-config.csv" file
    print("Importing ap-config.csv file")
    with open("ap-config.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        line_count = 0
        for row in csv_reader:
            print(f"\t{row[0]}, {row[1]}, {row[2]}, {row[3]}")
            ap_tags += """
                <ap-tag>
                    <ap-mac>""" + row[0] + """</ap-mac>"""
            if row[1] != "":
                ap_tags += """
                    <policy-tag>""" + row[1] + """</policy-tag>"""
            if row[2] != "":
                ap_tags += """
                    <site-tag>""" + row[2] + """</site-tag>"""
            if row[3] != "":
                ap_tags += """
                    <rf-tag>""" + row[3] + """</rf-tag>"""
            ap_tags += """
                </ap-tag>"""
            line_count += 1
        print(f"Processed {line_count} lines.\n")

    # Create a NETCONF template
    netconf_template = """
    <config>
        <ap-cfg-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-ap-cfg">
            <ap-tags>""" + ap_tags + """
            </ap-tags>
        </ap-cfg-data>
    </config>
    """

    # Print the NETCONF template
    print("NETCONF template for editing the AP tag configuration:\n{}".format(netconf_template))

    # Execute NETCONF edit_config() to edit the AP tag configuration
    result = m.edit_config(netconf_template, target = "running")

    # Parse the XML file
    xml_doc = xml.dom.minidom.parseString(result.xml)

    # Print the configuration
    print("NETCONF response for editing the AP tag configuration:\n{}".format(xml_doc.toprettyxml()))

def save_config(m):

    # Build XML Payload for the RPC
    save_body= '<cisco-ia:save-config xmlns:cisco-ia="http://cisco.com/yang/cisco-ia"/>'

    # Send the RPC to the device
    result = m.dispatch(xml_.to_ele(save_body))

    # Parse the XML file
    xml_doc = xml.dom.minidom.parseString(result.xml)

    print("NETCONF save config response:\n{}".format(xml_doc.toprettyxml()))


def main():

    # Connect the NETCONF manager to the 9800 wireless controller
    m = manager.connect(host="192.168.203.10",
                    port=830,
                    username="netconf",
                    password="changeme",
                    hostkey_verify=False)

    # Get the server capabilities
    #capabilities = get_capabilities(m)

    # Get the YANG schema and write them to text files
    #modules = get_schemas(m, capabilities)

    # Get the full running configuration
    #get_full_config(m)

    # Get the AP tag configuration
    #ap_list = get_tags_config(m)

    # Write the AP tag configuration into a CSV file
    #csv_write(ap_list)

    # Edit one AP tag configuration
    #edit_config_one_AP(m)

    # Edit the AP tag configuration
    #edit_config(m)

    # Save the running configuration
    #save_config(m)

    # Close the NETCONF manager session
    m.close_session()

if __name__ == "__main__":
    start_time = time.time()
    print("** Starting Python script...\n")
    main()
    run_time = time.time() - start_time
    print("** Time to run: %s sec" % round(run_time,2))
