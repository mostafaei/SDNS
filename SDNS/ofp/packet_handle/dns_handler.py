
import pickle
from ryu.ofproto.ofproto_v1_3 import OFP_NO_BUFFER
from ryu.lib.packet import packet
from packet_handler import PacketHandler
from ryu.ofproto import ofproto_v1_3, ether
from scapy.all import DNS, DNSQR, DNSRR, dnsqtypes
from ryu.lib.packet import udp, arp, ethernet, ipv4
import struct
from utils.communication import Client, Server
from model.customer import Customer
from model.node import Controller
from netaddr import *
from utils.connection import Connection


__author__='Habib Mostafaei'

#This class is responsible to handle all DNS queries in SDNS.
class DNSQueryHandlerAlg2(PacketHandler):
    def __init__(self, pkt, in_port, data, datapath,controller,federazione,public_to_private_a,
                       public_to_private_b):
        PacketHandler.__init__(self, pkt)
        self._pkt = pkt
        self._datapath = datapath
        self._in_port = in_port
        self._data=data
        self._controller=controller
        self._federation=federazione
        self._public_to_private_a=public_to_private_a
        self._public_to_private_b=public_to_private_b
	
	
    def handle_packet(self):
        #print "controller",self._controller, "federation ip",self._federation[0].get_ip()
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)[0]
        """
        Handle DNS packet inside Controller. Each DNS packet carries with a udp packet. We used the DNS class of Scapy library to decode
        DNS queries.
        """
        pkt_dns=DNS(self._pkt[-1])
        cs=self._controller.get_customers() 
        print '-------T-ID------------',self._controller.get_transaction_id()
        if (pkt_udp.dst_port==53 and self._controller.get_transaction_id() is None) and pkt_dns.qd.qtype==1 and pkt_dns.qd.qname!=cs[0].get_ns_domain_name():
        #if pkt_udp.dst_port==53:
            self._controller.set_port_number(pkt_udp.src_port)
            self._controller.set_transaction_id(pkt_dns.id)
            self._controller.set_packet_ip(pkt_ip.dst)
            ofp =self._datapath.ofproto
            parser =self._datapath.ofproto_parser
            
            output = ofp.OFPP_TABLE
            match = parser.OFPMatch()
            actions=[parser.OFPActionOutput(output)]
            cs=self._controller.get_customers() 
            new_pkt=packet.Packet()
            new_pkt.add_protocol(ethernet.ethernet(src='00:aa:00:00:0f:11',dst=cs[0].get_as_pe_mac()))
            new_pkt.add_protocol(pkt_ip)
            new_pkt.add_protocol(pkt_udp)
            new_pkt.add_protocol(self._pkt[-1])
            new_pkt.serialize()
            out = parser.OFPPacketOut(datapath=self._datapath, buffer_id=ofp.OFP_NO_BUFFER,in_port=3, actions=actions, data=new_pkt.data)
            self._datapath.send_msg(out)
            #self._controller.set_port_number(pkt_udp.src_port)
           


class DNSResponseHandlerAlg2(PacketHandler):
    def __init__(self, pkt, in_port, data, datapath,controller,federazione,public_to_private_a,public_to_private_b,pkt_dns):
        PacketHandler.__init__(self, pkt)
        self._pkt = pkt
        self._pkt_dns = pkt_dns
        self._datapath = datapath
        self._in_port = in_port
        self._data=data
        self._controller=controller
        self._federation=federazione
        self._public_to_private_a=public_to_private_a
        self._public_to_private_b=public_to_private_b
    def handle_packet(self):
        pkt_eth =self._pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)
        dns=DNS(self._pkt[-1])
        cs=self._controller.get_customers() 
        nsdomain=cs[0].get_ns_domain_name()
         
        if dns.qr==1 and dns.ar.rrname!=cs[0].get_ns_domain_name():
            dns.id=self._controller.get_transaction_id()
            new_pkt=packet.Packet()
            new_pkt.add_protocol(ethernet.ethernet(src='00:aa:bb:00:0f:11',dst=cs[0].get_next_hop_mac()))
            new_pkt.add_protocol(ipv4.ipv4(dst=cs[0].get_name_server(),src=pkt_ip.src,proto=17))
            new_pkt.add_protocol(udp.udp(src_port=53, dst_port=self._controller.get_port_number()))
            new_pkt.add_protocol(dns)
            self.send_dns_response_packet(new_pkt,cs[0].get_datapath(),cs[0].get_ingress_port())
            
        if dns.qr==1 and cs[0].get_ns_domain_name()==dns.ar.rrname:
            #print '----------I am calling another controller------------'
            self.send_dns_response_to_controller(self._pkt)


    #Send the DNS query to the controller 
    def send_dns_response_to_controller(self,pkt):
        cl=Client()
        #print 'cl', cl
        msg = "dns_query_sep_" + pickle.dumps(pkt)
        cl.send_message(msg,self._federation[0].get_ip(),10000) 

    def send_dns_response_packet(self,pkt, datapath,port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data =pkt.data
        actions = [parser.OFPActionOutput(port=int(port))]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
        datapath.send_msg(out)
        self._controller.set_port_number(None)
        self._controller.set_transaction_id(None)
        self._controller.set_packet_ip(None)

class DNSResponseHandlerAlg2_2(PacketHandler):
    def __init__(self, pkt, in_port, data, datapath,controller,federazione,public_to_private_a,public_to_private_b,pkt_dns):
        PacketHandler.__init__(self, pkt)
        self._pkt = pkt
        self._pkt_dns = pkt_dns
        self._datapath = datapath
        self._in_port = in_port
        self._data=data
        self._controller=controller
        self._federation=federazione
        self._public_to_private_a=public_to_private_a
        self._public_to_private_b=public_to_private_b
        PacketHandler.__init__(self, pkt)
        self._controller = controller
	
    def handle_packet(self):
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        self._controller.set_packet_ip(pkt_ip.dst)
        self.send_dns_response_to_controller(self._pkt)

    #Send the DNS query to the controller 
    def send_dns_response_to_controller(self,pkt):
        cl=Client()
        msg = "dns_response_sep_" + pickle.dumps(pkt)
        cl.send_message(msg,self._federation[0].get_ip(),10000)
        
         
#This class is responsible to handle all DNS queries in SDNS.
class DNSQueryHandler(PacketHandler):
    def __init__(self, pkt, in_port, data, datapath,controller,federazione,public_to_private_a,
                       public_to_private_b):
        PacketHandler.__init__(self, pkt)
        self._pkt = pkt
        self._datapath = datapath
        self._in_port = in_port
        self._data=data
        self._controller=controller
        self._federation=federazione
        self._public_to_private_a=public_to_private_a
        self._public_to_private_b=public_to_private_b
	
	
    def handle_packet(self):
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)[0]
        """
        Handle DNS packet inside Controller. Each DNS packet carries with a udp packet. We used the DNS class of Scapy library to decode
        DNS queries.
        """ 
       
        pkt_dns=DNS(self._pkt[-1])
        print ('-------T-ID------------',self._controller.get_transaction_id())
        if pkt_udp.dst_port==53 and pkt_dns.qd.qtype==1 and self._controller.get_transaction_id() is None:
            self._controller.set_transaction_id(pkt_dns.id)
            self._controller.set_port_number(pkt_udp.src_port)
            print '-------------Sent query with ID------', pkt_dns.id
            if pkt_dns:
                new_pkt=packet.Packet()
                new_pkt.add_protocol(ethernet.ethernet(src='00:00:00:00:0f:11'))
                new_pkt.add_protocol(ipv4.ipv4(src=self._controller.get_ip(),dst=self._federation[0].get_ip(),proto=17))
                new_pkt.add_protocol(udp.udp(src_port=12345, dst_port=53))
                new_pkt.add_protocol(self._pkt[-1])
                new_pkt.serialize()
                self.send_dns_query_to_controller(new_pkt)
                    
    
    #Send the DNS query to the controller 
    def send_dns_query_to_controller(self,pkt):
        cl=Client()
        msg = "dns_query_sep_" + pickle.dumps(pkt)
        cl.send_message(msg,self._federation[0].get_ip(),10000) 


class DNSResponseHandler(PacketHandler):
    def __init__(self, pkt, in_port, data, datapath,controller,federazione,public_to_private_a,public_to_private_b,pkt_dns):
        PacketHandler.__init__(self, pkt)
        self._pkt = pkt
        self._pkt_dns = pkt_dns
        self._datapath = datapath
        self._in_port = in_port
        self._data=data
        self._controller=controller
        self._federation=federazione
        self._public_to_private_a=public_to_private_a
        self._public_to_private_b=public_to_private_b
    	
    def handle_packet(self):
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)
        dns=DNS(self._pkt[-1])
        dnsrr = dns.an[0]
        if dns.qr==1:
            self.send_dns_response_to_controller(self._pkt)

            
    #Send the DNS query to the controller 
    def send_dns_response_to_controller(self,pkt):
        cl=Client()
        #print 'cl', cl
        msg = "dns_response_sep_" + pickle.dumps(pkt)
        cl.send_message(msg,self._federation[0].get_ip(),10000) 
        #print 'pkt DNS  sent to controller'

