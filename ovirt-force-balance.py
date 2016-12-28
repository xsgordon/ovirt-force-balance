#!/bin/python

import argparse
from math import ceil
from math import floor
from time import sleep
from ovirtsdk.api import API


def _parseArguments():

    parser = argparse.ArgumentParser(description="Automatically balance virtual" +
                                     "machine loads in an oVirt or " +
                                     "RHEV environment.")
    parser.add_argument("-l", "--location", action="store",
                        default="https://127.0.0.1:8443")
    parser.add_argument("-u", "--user", action="store", default="admin@internal")
    parser.add_argument("-p", "--password", action="store", required=True)
    parser.add_argument("-c", "--cluster", action="store", required=False)
    parser.add_argument("-K", "--key-file", action="store", required=False)
    parser.add_argument("-C", "--cert-file", action="store", required=False)
    parser.add_argument("-A", "--ca_file", action="store", required=False)
    parser.add_argument("-I", "--insecure", action="store_true", required=False)

    return parser.parse_args()


def _balanceCluster(cluster):

    print "Attempting to balance %s cluster (%s):" % (cluster.name, cluster.id)

    # Determine how many hosts and how many virtual machines are in the
    # environment. Use this to determine the ideal number of virtual machines
    # per host.

    host_list = api.hosts.list(query="cluster = %s and status = up" %
                               cluster.name)

    active_hosts = len(host_list)
    active_vms = len(api.vms.list(query="cluster = %s and status = up" %
                                  cluster.name))

    if active_hosts == 0:
        print "No active hosts in cluster %s to balance." % cluster.name
        return

    ideal_load = active_vms / active_hosts
    ideal_min = floor(ideal_load * 0.90)
    ideal_max = ceil(ideal_load * 1.10)

    # Display inputs to the calculation and the resultant range.
    print "Active Hosts: %s" % str(active_hosts)
    print "Active Virtual Machines: %s" % str(active_vms)
    print "Ideal Virtual Machines per host: %s to %s" % (str(ideal_min),
                                                         str(ideal_max))

    if active_hosts == 1:
        return

    # Loop through the hosts looking at the number of active VMs indicated. For
    # each host determine if it is over/under utilized. For over utilized
    # engage migration of enough VMs to bring it within range, for under
    # utilized just skip with a message. This is a "dumb" approach in that
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


try:
    args = _parseArguments()

    api = API(url=args.location,
              username=args.user,
              password=args.password,
              key_file=args.key_file,
              cert_file=args.cert_file,
              ca_file=args.ca_file,
              insecure=args.insecure)


    if args.cluster is None:

        clusters = api.clusters.list()

        for cluster in clusters:
            _balanceCluster(cluster)

    else:

        clusters = api.clusters.list(query="name = %s" % args.cluster)

        for cluster in clusters:
            _balanceCluster(cluster)

except Exception as ex:
    print "Unexpected error: %s" % ex
