from ofp.packet_handle.factory_packet_handler import FactoryPacketHandler

__author__ = 'gab'

import os

import eventlet

from ryu.ofproto import ofproto_v1_3, ether
from ryu.ofproto.ofproto_v1_3 import OFP_NO_BUFFER
from ryu.lib.packet import packet, ethernet, arp
from utils.parser import Parser
from utils.communication import Server, Client

# SYS_CONFIG = "conf/systemC1.conf"

"""
This class represents the system (in accord with Controller pattern)
"""


class System(object):
    def __init__(self, listen_port, path):

        self._controller_listen_port = listen_port
        # Root directory of the controller
        self._sys_root = os.path.dirname(os.path.abspath(__file__))
        # Load system configuration
        self._system_conf = self._sys_root + "/" + path
        self._federazione = None
        self._customers = None
        self._dp_to_customer = {}  # chiave :(id datapath, ingress_port) valore: customer
        self._controller = None

        # Create parser object
        self._parser = Parser(self._controller_listen_port)

    def load_system_configuration(self):
        # Start parser
        self._parser.load(self._system_conf)
        self._federazione = self._parser.get_federazione()
        self._customers = self._parser.get_customers()
        self._controller = self._parser.get_controller()

    def get_controller_info(self):
        return self._controller
    def init(self, public_to_private_a, public_to_private_b):

        server = Server(self._controller_listen_port, self._controller.get_ip(), self._controller, public_to_private_a,
                        public_to_private_b)
        eventlet.spawn(server.run)

    def add_node(self, datapath, ip):
        print"Controller : " + self._controller.get_name() + " ip: " + self._controller.get_ip() + " Pool ip pubblici: " + self._controller.get_public_subnet().__str__()
        for customer in self._controller.get_customers():
            # Identifico il datapath tramite l'ip
            if customer.get_ip_datapath() == ip:
                customer.set_datapath(datapath)
                self._dp_to_customer[datapath.id, customer.get_ingress_port()] = customer
                # print "Aggiunto datapath id: " + str(
                        # datapath.id) + " ip: " + ip + " porta di ingresso: " + customer.get_ingress_port() + " al customer: " + customer.get_name()

        print "Federation: "
        print self._federazione
        print "Customer: "
        print self._customers
     #   print self._dp_to_customer
        #Ask ce MAC address to send DNS queries--->Habib
        cs=self._controller.get_customers()
        #print '-------cs-------' ,cs[0]
        # print 'ofproto', cs[0].get_datapath() 
        if cs[0].get_ns_domain_name() is None:
            self.send_arp_request(cs[0].get_datapath(),cs[0].get_next_hop(),cs[0].get_ingress_port())
        else:
            self.send_arp_request(cs[0].get_datapath(),cs[0].get_next_hop(),cs[0].get_ingress_port())
            self.send_arp_request(cs[0].get_datapath(),cs[0].get_router(),cs[0].get_out_port())


    def handle_packet(self, pkt, dpid, in_port, data, datapath, public_to_private_a, public_to_private_b):
        fph = FactoryPacketHandler.get_instance()
        handler = fph.create_handler(pkt, self._dp_to_customer, in_port, data, datapath, self._controller,
                                     self._federazione, public_to_private_a, public_to_private_b)
        # print '@@@@@@@@@@@@@@@@@@@@@@@ Handler', type(handler)
        handler.handle_packet()

    #Send arp request to get MAC for DNS packets --->Habib
    def send_arp_request(self,datapath,dstip,port):
        #Controller sends the DNS packet to destination name server via controller by creating a DNS query
        new_pkt=packet.Packet()
        new_pkt.add_protocol(ethernet.ethernet(ethertype=ether.ETH_TYPE_ARP,src='9f:ff:ff:ff:ff:ff', dst='ff:ff:ff:ff:ff:ff'))
        new_pkt.add_protocol(arp.arp(hwtype=1,proto=0x800,hlen=6,plen=4,opcode=arp.ARP_REQUEST,src_mac='9f:ff:ff:ff:ff:ff',dst_mac='ff:ff:ff:ff:ff:ff',src_ip=self._controller.get_ip(),dst_ip=dstip))
        self.send_arp_packet(datapath,new_pkt,port)
         
    #Send the DNS packet to the destination name server
    def send_arp_packet(self, datapath,pkt,port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(port=int(port))]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=datapath.ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=data)
        datapath.send_msg(out)
        # print '-----ARP Request Sent--------'

