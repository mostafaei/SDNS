from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import arp
from arp_handler import ArpHandler
from ip_handler import IpHandler
from dns_handler import DNSQueryHandlerAlg2, DNSResponseHandlerAlg2, DNSResponseHandlerAlg2_2, DNSQueryHandler, DNSResponseHandler
from scapy.all import DNS, DNSQR, DNSRR, dnsqtypes
import struct

__author__ = 'robertodilallo-HabibMostafaei'


class FactoryPacketHandler(object):
    __instance = None

    def __init__(self):
        self._handler = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = FactoryPacketHandler()
        return cls.__instance

    def create_handler(self, pkt, dp_to_customer, in_port, data, datapath, controller, federazione, public_to_private_a,
                       public_to_private_b):
        print 'publice to private a',public_to_private_a,'publice to private',public_to_private_b
        cs=controller.get_customers() 
        arp_header = pkt.get_protocol(arp.arp)
        ip_header = pkt.get_protocol(ipv4.ipv4)
        udp_header = pkt.get_protocol(udp.udp)
        if arp_header is not None:
            self._handler = ArpHandler(pkt, datapath, in_port,controller) 
        #print('------pkt-------',pkt)
        #dns_pkt=DNS(pkt[-1])
        if udp_header is not None:
            print ('-----------',cs[0].get_ns_domain_name())
            dns_pkt=DNS(pkt[-1])
            if cs[0].get_ns_domain_name() is None:
                print '--calling alg1---'
                if dns_pkt.qr==0:
                    self._handler = DNSQueryHandler(pkt, in_port, data, datapath, controller, federazione,public_to_private_a, public_to_private_b)
                elif dns_pkt.qr==1:
                    self._handler = DNSResponseHandler(pkt, in_port, data, datapath, controller, federazione,public_to_private_a, public_to_private_b,pkt[-1])
            else:
                print '--calling alg2---'
                if dns_pkt.ancount==1:
                    dnsrr=dns_pkt.an
                    controller.set_packet_ip(ip_header.src)
                    self._handler = DNSResponseHandlerAlg2_2(pkt, in_port, data, datapath, controller, federazione,public_to_private_a, public_to_private_b,pkt[-1])
                elif dns_pkt.qr==0:
                    self._handler = DNSQueryHandlerAlg2(pkt, in_port, data, datapath, controller, federazione,public_to_private_a, public_to_private_b)
                elif dns_pkt.qr==1 and dns_pkt.qd.qname!=cs[0].get_ns_domain_name():
                    #print ('--dns.id------',dns_pkt.id,'----udp_dst_port_--',udp_header.dst_port,'----udp_src_port_--',udp_header.src_port)
                    self._handler = DNSResponseHandlerAlg2(pkt, in_port, data, datapath, controller, federazione,public_to_private_a, public_to_private_b,pkt[-1])
        else:
            ip_header = pkt.get_protocol(ipv4.ipv4)
            if ip_header is not None:
                self._handler = IpHandler(pkt, dp_to_customer, in_port, data, datapath, controller, federazione,
                                      public_to_private_a, public_to_private_b)
        return self._handler
