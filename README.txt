#############################################################################
###
### SDNS: a prototype SDN controller to handle DNS traffic in a federated 
###network.
###
### The DNS part of this software has been developed by Habib Mostafaei
### on top of SDN-VPN project within the research line described at
### http://www.dia.uniroma3.it/~compunet/www/view/topic.php?id=sdn
###
### Last update: 9 January 2017
#############################################################################

This is a documentation that describes how to set up a simulation 
scenario with NetKit in order to run our controllers. The NetKit 
includes all required software pieces to carry on such an experiment 
including: OpenvSwitch, Ryu, and Bind. We provide the backbone 
configuration to run our experiments as well as providing a script to 
generate a set of customized end hosts for each customer and a script 
to test our controllers.

=== GETTING STARTED ===

1. Install the experimental version of NetKit.

You can find all documents for installing NetKit in the below link;

http://wiki.netkit.org/index.php/Download_Official

You need the core scripts from the Latest Stable Release to use it. Moreover, 
you need to invoke vstart with option --append=root=98:0 and lstart with 
option --pass=--append=root=98:0.

You can follow the instruction to install NetKit. Note that it is mandatory 
to install NetKit on a system with a kernel version higher than 4 as well as 
on a linux 64 distribution.
After installing NetKit to switch from stable version to the experimental one 
(and viceversa), the following commands need to be executed.
  
 
a.  Enter into netkit file system folder  
    cd /opt/netkit/fs  
 
b.  To switch from stable to experimental  
    ln -sf netkit-fs-sid-x86_64 netkit-fs  
 
b.1 To switch from experimental to stable  
    ln -sf netkit-fs-i386-F5.2 netkit-fs  
 
c.   Enter into netkit kernel folder  
    cd /opt/netkit/kernel  
 
d.  To switch from stable to experimental  
    ln -sf modules-exp modules  
    ln -sf netkit-kernel-4.0.0-x86_64 netkit-kernel  
 
d.1 To switch from experimental to stable  
    ln -sf modules-stable modules  
    ln -sf netkit-kernel-i386-2.6.26.5-K2.8 netkit-kernel  
 
Note that:  
 - command a and c are always needed;  
 - command b and d are only needed to switch from stable to experimental  
 - commands c.1 and d.1 are only needed to switch from experimental to 
stable.

*************************************************************************
***********************IMPORTANT NOTE************************************
In order to be able to run all machines correctly with NetKit it is 
suggested to set "VM_MEMORY=128" in netkit.conf file inside the installed
NetKit directory. For example, to run the sw1, sw2, controller1, and 
controller2 VMs, this parameter must be 128. Generaly, it is suggested to
run the lab on a machine with a memory more than 6GB of RAM specially for
testing scalability of our approaches.
*************************************************************************
*************************************************************************

2. Pick a customized number of hosts

Enter directory “SDNSlab” on your machine edit “createHosts” based on 
your need. In this file, the “HostCount” variable determines how many end-
hosts you want to create for each customer. You can execute it by typing:

$./createHosts.sh

This script creates a customized number of end-hosts for each customer in a 
federated network as well as configuring their interfaces in “lab.conf” file. 
Also, it adds the IP address of each end-host to its local name server 
configuration which is accessible by going to directory “/etc/bind/”. 
Generally, this script creates a directory for each end-host, set up an 
interface for each end-host by connecting it to the CE, makes a copy of 
resolv.conf file inside “/etc/” directory of each end-host, and changes 
“lab.conf” file in order to connect the end-hosts to local name servers (i.e. 
ns1 and ns2) and customer premises (i.e. ce1 and ce2).

3. Run the lab

Now, the lab is ready to run by NetKit. Run the generated lab by typing:

$ lstart --pass=--append=root=98:0

Alternatively, if you want to run the lab in parallel you can use ‘–p4’ 
option with NetKit because it supports starting the virtual machines 
simultaneously.

$ lstart –p4 --pass=--append=root=98:0

After running the lab, you have to do a manual setting on ce1 and ce2 
machines in order to forward their default traffic to Openvswitch (e.g. sw1 
and sw2). To do that, type this command on sw1 and sw2;

$ ip a s

This creates a report for the interfaces and their IP and MAC addresses. Now, 
you have to direct default traffic to sw1 and sw2. For this purpose you have 
to enter to ce1 and ce2 console by selecting these machines and run the 
following commands, respectively;

ce1@ arp –s 10.1.0.2 “MAC address of eth0 on sw1”
ce2@ arp –s 20.1.0.13 “MAC address of eth1 on sw2”


4. Configure Ryu to run our controllers:

To run our controllers you have to add one option to the Ryu source. Inside 
each controller virtual machine you have to modify the flags file in 
“/opt/ryu/flags.py”. You have to add below line after “CONF.register_cli_opts([” 
line:

cfg.StrOpt(‘federated’),

save this modification.

5. Run the controllers.

To run each controller you have to go to the lab directory by typing:

Controller1@: cd /hostlab/controllers/SDNS/
Controller2@: cd /hostlab/controllers/SDNS/

The codes of the controllers placed here. 

Now, you can start the controllers by typing:

Controller1@: ryu-manager --federated conf/system_dns_c1_alg1.conf main.py

And the same procedure can be done for the second controller by typing;

Controller2@: ryu-manager --federated conf/system_dns_c1_alg1.conf main.py

The controllers are running now and we can do our tests. The instructions above 
will start full-configuration approach while for running the partial
configuration aaproach you can do as follows;

Controller1@: ryu-manager --federated conf/system_dns_c1_alg2.conf main.py
Controller2@: ryu-manager --federated conf/system_dns_c1_alg2.conf main.py


6. Test our controllers:

To test our controllers you can start to query one the end-host on the other 
customer site. For example, we want to query h2.c2.isp2.it from h1. For this 
purpose you can type:

h1@ ping –c1 h2.c2.isp2.it.

There is a script also for this goal to test our controllers’ scalabilities. 
You can exploit the “generatePing.sh” script to ping all machines on other 
customer side. To run this script you have to customize the parameters. In 
this file the variable “HostCount” determines how many end-host we have 
inside our customer side. The variable “C” determines which is the target 
customer to run the DNS queries. For instance, you want to query the end-
hosts of customer 2 from customer one. For this purpose, you have to set this 
parameter with a value of 2. Otherwise, if you want to query the end-hosts of 
customer 1 from customer 2, you have to set this parameter with 1.

To query all end-hosts with this script you have to enter the console of end-
hosts on each customer and type the following command. Suppose that from h1 
of customer 1, we want to query all end hosts of customer 2.

h1@ cd /hostlab

Now, you are in the lab directory of NetKit and you have access to all files 
inside this directory. To execute the DNS queries type;

h1@ ./generatePing.sh

It starts to query the end hosts of customer 2 and provides the proper DNS 
answer for each end host. 





