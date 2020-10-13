# 9800-NETCONF-script
Python script to retrieve and edit Access Point tags configuration on Cisco Catalyst 9800 wireless controller.

This script allows to connect to a Cisco Catalyst 9800 and perform the following operations:
* Get NETCONF capabilities of the Cisco 9800 wireless controller
* Import YANG schemas
* Export the static AP tags configuration for Access Points on Cisco 9800
* Edit the AP tags configuration
    
Go to the main() procedure and comment/uncomment the different tasks

    # Connect the NETCONF manager to the 9800 wireless controller
    m = manager.connect(host="192.168.203.10",
                    port=830,
                    username="netconf",
                    password="changeme",
                    hostkey_verify=False)

    # Get the server capabilities
    capabilities = get_capabilities(m)

    # Get the YANG schema and write them to text files
    modules = get_schemas(m, capabilities)

    # Get the full running configuration
    get_full_config(m)

    # Get the AP tag configuration
    ap_list = get_tags_config(m)

    # Write the AP tag configuration into a CSV file
    csv_write(ap_list)

    # Edit one AP tag configuration
    edit_config_one_AP(m)

    # Edit the AP tag configuration
    edit_config(m)

    # Save the running configuration
    save_config(m)

    # Close the NETCONF manager session
    m.close_session()

The tool is supported to run on Python 3.8 or newer. 

More information can be found at https://dot11zen.blogspot.com
