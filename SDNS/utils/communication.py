__author__ = 'gab'

import pickle

import socket
from utils.connection import Connection
from netaddr import *
from ofp.packet_handle.controller_dns_handler import ControllerDNSHandlerAlg2, ControllerDNSResponseHandlerAlg2, ControllerDNSHandler, ControllerDNSResponseHandler
SYS_CONFIG = "conf/systemC1.conf"

"""
This class represents ServerSocket, used by the controller to listening to new connection
with other controllers.
"""


class Server():
    def __init__(self, listen_port, ip, controller, public_to_private_a, public_to_private_b):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind((ip, listen_port))
        self._server_socket.listen(5)
        self._controller = controller
        self._public_to_private_a = public_to_private_a
        self._public_to_private_b = public_to_private_b
        #self._datapath=None

    def run(self):
        # Create a thread to wait for new connection
        print 'Socket pronta per accettare nuove connesioni da altri Controller'
        while 1:
            (socket_client, address) = self._server_socket.accept()
            data = socket_client.recv(4096)
            self.process_data(data)

    def process_data(self, data):
        print "This message is received" #: \n" + data
        #msg_type = data.split("_sep_")
        msg_type, msg = data.split("_sep_")
        #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", len(msg_type), msg_type
        cs=self._controller.get_customers()
        if msg_type == "binding":
            src, dst = msg.split(",")
            src, private_address_src, public_address_src = src.split(":")
            dst, private_address_dst, public_address_dst = dst.split(":")
            connection = Connection()
            for customer in self._controller.get_customers():
                if customer.get_private_ip_subnet().__contains__(IPAddress(private_address_dst)):
                    connection.addStaticRoute(customer.get_router(),
                                              "sudo route add -host " + public_address_dst + " gw " + customer.get_next_hop() + " dev eth2",
                                              public_address_dst)
            self._public_to_private_a[public_address_dst] = private_address_dst
            self._public_to_private_b[public_address_src] = private_address_src
        elif msg_type == "dns_query" and cs[0].get_ns_domain_name() is not None:
            dns_query = pickle.loads(msg)
            counter=self._controller.get_packet_counter()
            counter=counter+1
            counter=self._controller.set_packet_counter(counter)
            CDNS=ControllerDNSHandlerAlg2(dns_query,self._controller)
            CDNS.handle_socket_msg() 
        elif msg_type == "dns_response" and cs[0].get_ns_domain_name() is not None:
            #print '########################## DNS Packet has been recieved.'
            counter=self._controller.get_packet_counter()
            counter=counter+1
            counter=self._controller.set_packet_counter(counter)
            dns_query = pickle.loads(msg)
            CDNS=ControllerDNSResponseHandlerAlg2(dns_query,self._controller)
            CDNS.handle_socket_msg() 

        elif msg_type == "dns_query" and cs[0].get_ns_domain_name() is None:
            #print '########################## DNS Packet has been recieved.'
            dns_query = pickle.loads(msg)
            CDNS=ControllerDNSHandler(dns_query,self._controller)
            CDNS.handle_socket_msg() 
        elif msg_type == "dns_response" and cs[0].get_ns_domain_name() is None:
            dns_query = pickle.loads(msg)
            CDNS=ControllerDNSResponseHandler(dns_query,self._controller)
            CDNS.handle_socket_msg() 

class Client():
    def __init__(self):
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_message(self, message, ip, port):
        #self._datapath=datapath
        print 'Hi from send_message', ip, port
        self._client_socket.connect((ip, port))
        print "Controller connection established"
        #print 'message', message
        self._client_socket.send(message)
        print "Messaggio sent"
        self._client_socket.close()
        print "Socket closed"
