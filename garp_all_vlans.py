# coding=utf-8
# Copyright (C) 2016 Intelligent Visbility, Inc. - Richard Collins
# <richardc@intelligentvisibility.com>

import netifaces
import signal
import subprocess
import sys
import time

"""
This script can be run on an Arista EOS switch to cause all SVI interfaces to
generate gratuitous ARP messages out all VLAN interfaces at a desired
interval.  It can be used in a variety of situations such as migration of
layer 3 services from other devices to an Arista switch were you need to
notify all endpoints to use the new Arista default gateway for example.

"""

# set the frequency of pings in seconds to send (CTRL-C allows for early
# termination when desired) (ex: can use .5 for 500ms between garps)
GARP_INTERVAL = 1


def kill_popen_list(popen_list):
    """
    Terminate all PIDs in a list
    :param popen_list: list() of subprocess PIDs
    """
    for process in popen_list:
        process.kill()
        sys.exit(0)


def signal_handler(signal, frame):
    """
    register a signal handler to catch SIGINT and kill all the child arping
    processe
    """
    print('CTRL-C was pressed!\n\nKilling child processes...')
    kill_popen_list(process_list)


signal.signal(signal.SIGINT, signal_handler)

# pull a list of all interfaces on the switch
interface_list = netifaces.interfaces()
"""build a list of tuples as (interface, ipaddress) to be used for calling
arping on all vlan interfaces only"""
target_list = [(interface, netifaces.ifaddresses(interface)[2][0]['addr']) for
               interface in interface_list if
               str(interface)[:4].lower() == 'vlan']

""" This is just a safety net.  If arping hangs or doesn't exit cleanly,
we do not want to create an infinite # of arping processes on the switch and
impact production while running in our infinite loop.  So, we will track each
PID in a list, and verify the PID has terminated for all vlans before running
another batch of arping processes.  If it hangs, we do not do the next round
of pings.  This errs ensures the process fails closed vs open."""
process_list = []

# send at requested intervals and wait for CTRL-C to interrupt
while True:
    # kick off a ping on each interface and store the list of processes
    for target_network in target_list:
        process_list.append(
                subprocess.Popen(['/sbin/arping', '-A', '-c', '1', '-I',
                                  str(target_network[0]),
                                  str(target_network[1])]))
    # ensure that all the processes have exited
    while len(process_list):
        for process in process_list:
            if process.poll() is not None:
                process_list.remove(process)
        time.sleep(.1)
    # sleep for requested interval before sending the next wave of pings
    time.sleep(GARP_INTERVAL)
