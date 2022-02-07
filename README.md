Arista EOS GARP all VLAN Script
---
This script has been useful for us in cases where we need to migrate L3 services onto Arista devices from existing networks during migrations.  Hopefully it's useful to others as well!

Use-case example:
- an existing router or switch holds all L3 default gateways for numerous VLANs
- you want to migrate the existing VLAN L3 addresses onto an Arista EOS device while:
    - not requiring end hosts to clear their ARP tables when the MAC of the gateway changes
    - minimize service disruption to hosts when the old L3 interfaces are shut down

To achieve this:
- Disable any existing GARP funtionality on the old gateways
    - HSRP for example will try to GARP to handle duplicate address situations and can fight the new EOS instance for control
- Activate all L3 interfaces on the new Arista EOS devices using the existing IP addresses from the old network
- Run this script to allow the EOS device to begin notifying all hosts of the MAC change for the gateway address
    - NOTE: If using VARP or virtual-router, this only needs to be run on any one switch which holds the virtual MAC address during the migration.
- Verify that hosts are using the new EOS VLAN addresses
- Shut down the old switch/router VLAN interfaces



####This script has been tested on Arista EOS 4.15.5M and 4.18.2F
**Pre-reqs:**

This script uses the `netifaces` pthon package to quickly pull all interfaces for 
the switch with correspondig attributes such as IP address.  Since old versions of EOS 
do not have pip installed by default, you may need to manually install the Fedora rpm 
for the python netinterfaces library into EOS: 
- it can be obtained from [HERE](<https://www.rpmfind.
  net/linux/RPM/fedora/24/i386/p/python-netifaces-0.10.4-4.fc24.i686.html>) or you 
  may need to find the RPM that targets the underlying Fedora release for your older 
  version of EOS
- The RPV can be installed from bash on the switch using `sudo rpm -U 
  python-netifaces-0.10.4-4.fc24.i686.rpm`

  
- Alternatively you can simply do `python3 -m pip install netifaces` on later editions
  of EOS if your switch can access PYPI
 

- the installation will not survive a device reboot by default.  If this is something you need to use in an ongoing basis, use normal EOS processes to store the package in persistent storage and have it installed upon each boot.
    
