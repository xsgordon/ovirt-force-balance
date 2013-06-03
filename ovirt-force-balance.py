#!/bin/python

from ovirtsdk.api import API
from ovirtsdk.xml import params
import argparse

parser = argparse.ArgumentParser(description="Automatically balance virtual" +
                                             "machine loads in an oVirt or " +
                                             "RHEVenvironment.")
parser.add_argument("-l", "--location", action="store",
                    default="https://127.0.0.1:8443")
parser.add_argument("-u", "--user", action="store", default="admin@internal")
parser.add_argument("-p", "--password", action="store", required=True)
args = parser.parse_args()

try:
    api = API(url=args.location,
              username=args.user,
              password=args.password,
              insecure=True)

    # Determine how many hosts and how many virtual machines are in the
    # environment. Use this to determine the ideal number of virtual machines
    # per host. Note that this is currently a "dumb" calculation in that it
    # assumes one cluster for the entire environment.
    active_hosts = int(api.get_summary().get_hosts().active)
    active_vms = int(api.get_summary().get_vms().active)
    ideal_load = active_vms / active_hosts
    ideal_min = ideal_load * 0.90
    ideal_max = ideal_load * 1.10

    # Display inputs to the calculation and the resultant range.
    print "Active Hosts: %s" % str(active_hosts)
    print "Active Virtual Machines: %s" % str(active_vms)
    print "Ideal Virtual Machines per host: %s to %s" % (str(ideal_min),
                                                         str(ideal_max))

    # Obtain a list of hosts being sure to retrieve all pages.
    host_list = []
    host_page_index = 1
    host_page_current = api.hosts.list(query="page %s" % host_page_index)

    while(len(host_page_current) != 0):
        host_list = host_list + host_page_current
        host_page_index = host_page_index + 1
        try:
            host_page_current = api.hosts.list(query="page %s" %
                                               host_page_index)
        except Exception as ex:
            print "Error retrieving page %s of list: %s" % (host_page_index,
                                                            ex)

    # Loop through the hosts looking at the number of active VMs indicated. For
    # each host determine if it is over/under utilized. For over utilized
    # engage migration of enough VMs to bring it within range, for under
    # utilized just skip with a message. This is also a "dumb" approach in that
    # it works best in small clusters, in larger clusters a migration target
    # should really be specified otherwise you might just move VMs from one
    # over utilized host to another.
    for host in host_list:

        host_active = int(host.get_summary().active)

        if host_active > ideal_max:
            difference = host_active - ideal_max
            host_migrating = int(host.get_summary().migrating)

            print "Host %s is over-utilized" % host.name
            vms_list = api.vms.list(**{"host.id": host.id})
            for vm in vms_list:
                if difference > host_migrating:
                    vm.migrate()
                    print "Migrating '%s'." % vm.name
                    host_migrating = host_migrating + 1
                    sleep(60)
        elif host_active < ideal_min:
            print "Host %s is under-utilized" % host.name

except Exception as ex:
    print "Unexpected error: %s" % ex
