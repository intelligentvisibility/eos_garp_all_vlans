# coding=utf-8
# Copyright (C) 2016 Intelligent Visbility, Inc. - Richard Collins
# <richardc@intelligentvisibility.com>

import logging
import netifaces
import os
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

# set the frequency of pings in seconds to send (CTRL-C allows for early termination when desired)
# (ex: can use .5 for 500ms between garps)
ARPING_INTERVAL = 1
# flag to control output of ARPING.  True = stdout/stderr, False = send to /dev/null
ARPING_OUTPUT = False

# set logging level to desired output
logger = logging.basicConfig(level=logging.DEBUG)

RUN_FLAG = True  # used to by interrupt handlers to signal exit


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
    register a signal handler to catch SIGINT and kill all the child arping processes
    """
    print('CTRL-C was pressed!\n\nKilling child processes...')
    global RUN_FLAG
    RUN_FLAG = False
    kill_popen_list(process_list)


signal.signal(signal.SIGINT, signal_handler)

""" This is just a safety net.  If arping hangs or doesn't exit cleanly,
we do not want to create an infinite # of arping processes on the switch and
impact production while running in our infinite loop.  So, we will track each
PID in a list, and verify the PID has terminated for all vlans before running
another batch of arping processes.  If it hangs, we do not do the next round
of pings.  This errs ensures the process fails closed vs open."""
process_list = []

# main run loop; send at requested intervals and wait for CTRL-C to interrupt
while RUN_FLAG:
    start_time = time.time()
    logging.debug("Starting new ARPING for all VLAN interfaces")
    # pull a list of all interfaces on the switch
    interface_list = netifaces.interfaces()
    # build a list of tuples as (interface, ipaddress) to be used for calling arping on
    # all vlan interfaces
    target_list = [(interface, netifaces.ifaddresses(interface)[2][0]['addr']) for interface in interface_list if
                   str(interface)[:4].lower() == 'vlan']
    # kick off a ping on each interface and store the list of processes
    process_count = 0
    if not ARPING_OUTPUT:
        with open(os.devnull, 'w') as dev_null:
            for target_network in target_list:
                process_list.append(subprocess.Popen(
                    ['/sbin/arping', '-A', '-c', '1', '-I', str(target_network[0]), str(target_network[1])],
                    stdout=dev_null, stderr=subprocess.STDOUT))
                process_count += 1
    else:
        for target_network in target_list:
            process_list.append(subprocess.Popen(
                ['/sbin/arping', '-A', '-c', '1', '-I', str(target_network[0]), str(target_network[1])]))
            process_count += 1
    logging.debug("Started {} arping processes for {} interfaces.".format(process_count, len(target_list)))

    # ensure that all the processes have exited before continuing
    while len(process_list):
        for process in process_list:
            if process.poll() is not None:
                process_list.remove(process)
    logging.info("Execution time for all {} processes: {} seconds".format(process_count, time.time() - start_time))
    # sleep for requested interval before sending the next ping
    logging.info("Sleeping for {} seconds".format(ARPING_INTERVAL))
    time.sleep(ARPING_INTERVAL)
