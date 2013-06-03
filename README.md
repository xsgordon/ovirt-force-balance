oVirt and RHEV include cluster level policy options for ensuring an even
distribution of virtual machines is maintained across a cluster. These policies
are only engaged however when load on a single host reaches a given threshold
which is generally quite high.

In some environments it may be desirable to keep these thresholds high while
also maintaining a somewhat even spread of virtual machines across the hosts
in each cluster.

The **ovirt-force-balance** script forces the balancing of virtual machines
across an oVirt or RHEV environment. Currently this is done using relatively
"dumb" logic. Available CPUs and RAM are not compared to virtual machine
requirements, instead approximately equal hosts and virtual machine workloads
are assumed. Balancing is formed by determining the number of hosts and
virtual machines in the cluster. This is used to determine the optimum number
of virtual machines per host as virtual machines divided by hosts.

The script then loops through the hosts in the environment and for each over
utilized host initiates virtual machine migrations to bring the number of
virtual machines on the host down to the optimum number.

ovirt-force-balance --url URL --user USER --pass --percentage=M --sleep=n

TODO:

- Parameterize
- Add cluster parameter and logic.
- Target migrations to machines identified as under utilized.
