__author__ = 'gab'

from netaddr import *

"""
A customer is an object that models a subnet behind a datapath that needs to be natted in order
to reach a remote customer in another AS. Each customer is identified by a name, a private IP 
subnet, a public IP subnet (or just address) and the datapath's port connected to the rest of the 
AS.
"""


class Customer(object):
    def __init__(self, name, private_ip_subnet , ingress_port, ip_datapath,router,next_hop,out_port,datapath_to_router_ip,datapath_to_router_interface,ns_domain_name):
        self._ingress_port = ingress_port
        self._out_port = out_port
        self._ip_datapath = ip_datapath
        self._name_server = None
        self._datapath_to_router_ip= datapath_to_router_ip
        self._datapath_to_router_interface =datapath_to_router_interface
        self._name = name
        self._private_ip_subnet = IPNetwork(private_ip_subnet)
        self._datapath = None
        self._router = router
        self._next_hop = next_hop
        self._next_hop_mac = None
        self._as_pe_mac= None
        self._ns_domain_name=ns_domain_name

    def __hash__(self):
        return hash(self.dpid)

    def __repr__(self):
        return "Customer(Name=%s, Ingress_port=%s)" % (
            self._name, self._ingress_port)

    def get_name(self):
        return self._name
    
    def get_ns_domain_name(self):
        return self._ns_domain_name

    def get_private_ip_subnet(self):
        return self._private_ip_subnet

    def set_datapath(self, datapath):
        self._datapath = datapath

    def get_datapath(self):
        return self._datapath

    def get_router(self):
        return self._router

    def get_datapath_to_router_ip(self):
        return self._datapath_to_router_ip
    
    def get_datapath_to_router_interface(self):
        return self._datapath_to_router_interface
    def set_as_pe_mac(self,mac):
        self._as_pe_mac=mac

    def get_as_pe_mac(self):
        return self._as_pe_mac

    def set_next_hop_mac(self,mac):
        self._next_hop_mac=mac

    def get_next_hop_mac(self):
        return self._next_hop_mac

    def get_next_hop(self):
        return self._next_hop

    def set_name_server(self, name_server):
        self._name_server = name_server

    def get_name_server(self):
        return self._name_server

    def get_ingress_port(self):
        return self._ingress_port

    def get_out_port(self):
        return self._out_port

    def get_ip_datapath(self):
        return self._ip_datapath

class CustomerAlg1(object):
    def __init__(self, name, private_ip_subnet , ingress_port, ip_datapath,router,next_hop):
        self._ingress_port = ingress_port
        self._ip_datapath = ip_datapath
        self._name_server = None
        self._name = name
        self._private_ip_subnet = IPNetwork(private_ip_subnet)
        self._datapath = None
        self._router = router
        self._next_hop = next_hop
        self._next_hop_mac = None
        self._ns_domain_name=None

    def __hash__(self):
        return hash(self.dpid)

    def __repr__(self):
        return "Customer(Name=%s, Ingress_port=%s)" % (
            self._name, self._ingress_port)

    def get_name(self):
        return self._name

    def get_private_ip_subnet(self):
        return self._private_ip_subnet

    def set_datapath(self, datapath):
        self._datapath = datapath

    def get_datapath(self):
        return self._datapath

    def get_router(self):
        return self._router

    def set_next_hop_mac(self,mac):
        self._next_hop_mac=mac

    def get_next_hop_mac(self):
        return self._next_hop_mac

    def get_next_hop(self):
        return self._next_hop

    def set_name_server(self, name_server):
        self._name_server = name_server

    def get_name_server(self):
        return self._name_server

    def get_ingress_port(self):
        return self._ingress_port

    def get_ip_datapath(self):
        return self._ip_datapath
    def get_ns_domain_name(self):
        return self._ns_domain_name


