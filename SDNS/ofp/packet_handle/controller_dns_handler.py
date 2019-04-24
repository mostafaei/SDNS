import pickle
from ryu.ofproto.ofproto_v1_3 import OFP_NO_BUFFER
from ryu.lib.packet import packet
from packet_handler import PacketHandler
from ryu.ofproto import ofproto_v1_3, ether
from scapy.all import DNS, DNSQR, DNSRR, dnsqtypes
from ryu.lib.packet import udp, arp, ethernet, ipv4
from model.customer import Customer
from model.node import Controller
from netaddr import *
import socket

__author__='Habib Mostafaei'

#This class manages the DNS queries which one controller wants to send to other controller in order to ask 
#the right name server for the query 
class ControllerDNSHandlerAlg2(object):
    def __init__(self,pkt,controller):
        self._controller = controller
        self._pkt =pkt
	
    def handle_socket_msg(self):
        pkt_eth=self._pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)[0]
        pkt_dns=DNS(self._pkt[-1])
        print( '----------------Sent query with ID', pkt_dns.id,pkt_dns)
        if pkt_udp.dst_port==53 or pkt_udp.src_port==53:
            #print 'A DNS query for controller is received'
            if pkt_dns:
                cs=self._controller.get_customers() 
                d_mac= cs[0].get_next_hop_mac()
                pkt_dns.qr=0 
                 
                new_pkt=packet.Packet()
                e=ethernet.ethernet(dst=cs[0].get_next_hop_mac(),src=pkt_eth.src)
                new_pkt.add_protocol(e)
                new_pkt.add_protocol(ipv4.ipv4(src=self._controller.get_ip(),dst=cs[0].get_name_server(),proto=17))
                new_pkt.add_protocol(udp.udp(src_port=pkt_udp.dst_port, dst_port=pkt_udp.src_port))
                new_dns=DNS(rd=0,id=pkt_dns.id,qd=DNSQR(qname=pkt_dns.qd.qname),ns=DNSRR(rrname=pkt_dns.ar.rrname,type=1,ttl=60000,rdata=cs[0].get_name_server()))
                new_pkt.add_protocol(new_dns)
                new_pkt.serialize()
                self.send_dns_packet(new_pkt,cs[0].get_datapath(),cs[0].get_ingress_port())
    

    def send_dns_packet(self,pkt,datapath,port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #print( '***pkt inside send***', pkt)
        data =pkt.data
        actions = [parser.OFPActionOutput(port=int(port))]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
        datapath.send_msg(out)

        self._controller.set_port_number(None)
        self._controller.set_transaction_id(None)

#this class is responsibe for handling the received DNS responses from the target name server
#it has to forward this response to other controller which asked a DNS query       
class ControllerDNSResponseHandlerAlg2(object):
    def __init__(self,pkt,controller):
        self._controller = controller
        self._pkt =pkt
	
    def handle_socket_msg(self):
        pkt_eth=self._pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)[0]
        dns=DNS(self._pkt[-1])
        #print '---- I received a response with ID----', dns.id
        dnsrr = dns.an[0]
        if dns.qr==1:
            
            pool=self._controller.get_pool_fittizio()
            ip=IPNetwork(pool)            
            ip_list=list(ip)
            cs=self._controller.get_customers() 
            customer_ip=cs[0].get_private_ip_subnet()
          
            if IPAddress(dnsrr.rdata) in IPNetwork(customer_ip):
                new_response=str(ip_list[1]) 
                responseIP=dnsrr.rdata
                myip=list(responseIP.split('.'))
                index=myip[-1]
                responseIP=str(ip_list[int(index)])
                dns.ns[0].rrname='.'
                dns.ns[0].rrdata='.'
                dns.id=self._controller.get_transaction_id()
                cs=self._controller.get_customers() 
                new_pkt=packet.Packet()
                new_pkt.add_protocol(ethernet.ethernet(src='10:00:00:00:10:ff',dst=cs[0].get_next_hop_mac()))
                new_pkt.add_protocol(ipv4.ipv4(src=self._controller.get_packet_ip(),dst=cs[0].get_name_server(),proto=17))
                new_pkt.add_protocol(udp.udp(src_port=53, dst_port=self._controller.get_port_number()))
                dns.an[0].rdata=str(responseIP)
                dns.ar[0].rdata=str(ip_list[1]) 
                new_pkt.add_protocol(dns)
                print ('----------------The Number of Exchanged PACKETS between Controllers-----',self._controller.get_packet_counter()) 
                dnsrr = dns.an[0]
                new_pkt.serialize()
                self.send_dns_packet(new_pkt,cs[0].get_datapath(),cs[0].get_ingress_port())
    
    def send_dns_packet(self,pkt,datapath,port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        data =pkt.data
        self._controller.set_transaction_id(None)
        actions = [parser.OFPActionOutput(port=int(port))]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
        datapath.send_msg(out)


#This class manages the DNS queries which one controller wants to send to other controller in order to ask 
#the right name server for the query
class ControllerDNSHandler(object):
    def __init__(self,pkt,controller):
        self._controller = controller
        self._pkt =pkt
        
	
    def handle_socket_msg(self):
        pkt_eth=self._pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)[0]
        pkt_dns=DNS(self._pkt[-1])
        if pkt_udp.dst_port==53:
            print 'A DNS query for controller is received'
            if pkt_dns:
                cs=self._controller.get_customers() 
                #create a new DNS packet to send to the name server                
                new_pkt=packet.Packet()
                new_pkt.add_protocol(ethernet.ethernet(src='00:00:00:00:00:ff',dst=cs[0].get_next_hop_mac()))
                new_pkt.add_protocol(ipv4.ipv4(src=self._controller.get_ip(),dst=cs[0].get_name_server(),proto=17))
                new_pkt.add_protocol(udp.udp(src_port=22345, dst_port=53))
                new_pkt.add_protocol(self._pkt[-1])
                new_pkt.serialize()
                
                self.send_dns_packet(new_pkt,cs[0].get_datapath(),cs[0].get_ingress_port())
    

         
    #Send the DNS packet to the destination name server
    def send_dns_packet(self,pkt,datapath,port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        data =pkt.data
        actions = [parser.OFPActionOutput(port=int(port))]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
        datapath.send_msg(out)

#this class is responsibe for handling the received DNS responses from the target name server
#it has to forward this response to other controller which asked a DNS query
class ControllerDNSResponseHandler(object):
    def __init__(self,pkt,controller):
        self._controller = controller
        self._pkt =pkt
	
    def handle_socket_msg(self):
        pkt_eth=self._pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ip =self._pkt.get_protocols(ipv4.ipv4)[0]
        pkt_udp =self._pkt.get_protocols(udp.udp)[0]
        dns=DNS(self._pkt[-1])
        print '--------I received a response with ID-------', dns.id
        dnsrr = dns.an[0]
        if dns.qr==1:
            pool=self._controller.get_pool_fittizio()
            ip=IPNetwork(pool)            
            ip_list=list(ip)
            #print( '-----dns.an--------',dns.an[0])
            cs=self._controller.get_customers() 
            customer_ip=cs[0].get_private_ip_subnet()
          
            if IPAddress(dnsrr.rdata) in IPNetwork(customer_ip):
                new_response=str(ip_list[1]) 
                responseIP=dnsrr.rdata
                myip=list(responseIP.split('.'))
                index=myip[-1]
                responseIP=str(ip_list[int(index)])
                if dns.nscount>=1:
                    dns.ns[0].rrname='ROOT-SERVER'
                    dns.ns[0].rdata='30.0.0.3'
                if dns.arcount>=1:
                    dns.ar.rrname='ROOT-SERVER'
                    dns.ar.rdata='30.0.0.3'
                dns.id=self._controller.get_transaction_id()
                cs=self._controller.get_customers() 
                new_pkt=packet.Packet()
                new_pkt.add_protocol(ethernet.ethernet(src='10:00:00:00:10:ff',dst=cs[0].get_next_hop_mac()))
                new_pkt.add_protocol(ipv4.ipv4(src='30.0.0.3',dst=cs[0].get_name_server(),proto=17))
                new_pkt.add_protocol(udp.udp(src_port=53, dst_port=self._controller.get_port_number()))
                dns.an[0].rdata=str(responseIP)
                new_pkt.add_protocol(dns)
                #print '------------DNS-----------',new_pkt 
                new_pkt.serialize()
                self.send_dns_packet(new_pkt,cs[0].get_datapath(),cs[0].get_ingress_port())
    
    #Send the DNS packet to the destination name server
    def send_dns_packet(self,pkt,datapath,port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        data =pkt.data
        self._controller.set_transaction_id(None)
        actions = [parser.OFPActionOutput(port=int(port))]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
        datapath.send_msg(out)