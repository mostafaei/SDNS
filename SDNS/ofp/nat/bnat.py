__author__ = 'robertodilallo'


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import arp, ethernet, packet
from ryu.topology import event
from ryu.ofproto import ether
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ofp.nat.absnat import absnat
from netaddr import *


class bnat(absnat):

    def __init__(self):
        absnat.__init__(self)
        self.mapping_public_to_private_a = {}
        self.mapping_private_to_public_a = {}
        self.last_used_port_a = 1023
        self.mapping_public_to_private_b = {}
        self.mapping_private_to_public_b = {}
        self.last_used_port_b = 1023
        self._public_address_a = IPAddress('20.0.0.1')
        self._public_address_b = IPAddress('20.0.1.1')


    def get_binding_ce1a(self,private_address, private_port):
        if (private_address,private_port) in self.mapping_private_to_public_a:
             public_port = self.mapping_private_to_public_a[(private_address,private_port)]
        else:
             public_port = self.get_port_a()
        self.mapping_public_to_private_a[public_port]= (private_address, private_port)
        self.mapping_private_to_public_a[(private_address, private_port)]=public_port
        return (self._public_address_a, public_port)

    def get_binding_ce1b(self,private_address, private_port):
        if (private_address,private_port) in self.mapping_private_to_public_b:
             public_port = self.mapping_private_to_public_b[(private_address,private_port)]
        else:
             public_port = self.get_port_b()
        self.mapping_public_to_private_b[public_port]= (private_address, private_port)
        self.mapping_private_to_public_b[(private_address, private_port)]=public_port
        return (self._public_address_b, public_port)


    def get_private_ce1a(self, public_port):
        private_couple = self.mapping_public_to_private_a[public_port]
        return private_couple


    def get_private_ce1b(self, public_port):
        private_couple = self.mapping_public_to_private_b[public_port]
        return private_couple
        pass

    def print_binding(self):
        print 'A PORT TO IP', self.mapping_public_to_private_a
        print 'A IP TO PORT', self.mapping_private_to_public_a
        print 'B PORT TO IP', self.mapping_public_to_private_b
        print 'B IP TO PORT', self.mapping_private_to_public_b



    # def nat(self,pkt):
    #     private_address = pkt.get_protocol(ipv4.ipv4).src
    #     private_port = pkt.get_protocol(tcp.tcp).src_port
    #     if (private_address,private_port) in self.mapping_private_to_public:
    #         public_port = self.mapping_private_to_public[(private_address,private_port)]
    #     else:
    #         public_port = self.get_port()
    #     self.mapping_public_to_private[public_port]= (private_address, private_port)
    #     self.mapping_private_to_public[(private_address, private_port)]=public_port
    #     return (private_address,private_port,public_port)
    #
    #
    # def denat(self,pkt):
    #     public_port = pkt.get_protocol(tcp.tcp).dst_port
    #     private_address_and_port = self.mapping_public_to_private[public_port]
    #     private_address = private_address_and_port[0]
    #     private_port = private_address_and_port[1]
    #     return (private_address,private_port,public_port)


    def get_port_a(self):
        if (self.last_used_port_a < 65536):
            port = self.last_used_port_a+1
        else:
            port = 1024
        self.last_used_port_a = port
        return port

    def get_port_b(self):
        if (self.last_used_port_b < 65536):
            port = self.last_used_port_b+1
        else:
            port = 1024
        self.last_used_port_b = port
        return port












