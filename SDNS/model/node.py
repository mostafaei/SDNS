__author__ = 'gab'

from netaddr import *



"""
A controller is an object with a name, an IP address and a port used for communicating with other
controllers.
"""


class Controller(object):
    def __init__(self, name, ip, port, public_subnet):
        self._name = name
        self._public_subnet = IPNetwork(public_subnet)
        self._ip = ip
        self._transaction_id = None
        self._packet_ip = None
        self._packet_counter = 0
        self._port_number = None
        self._port = port  #porta di ascolto per connessioni con altri controller
        self._customers = []
        self._pool_fittizzi = None
        self._fittizio_to_private = {}

    def __repr__(self):
        return 'Controller(name=%s, addr=%s:%i)' % (self._name, self._ip, self._port)

    def set_customers(self, customer):
        self._customers.append(customer)

    def set_pool_fittizzi(self,pool):
        self._pool_fittizzi =  IPNetwork(pool)

    def set_fittizio(self,fittizio,private):
        self._fittizio_to_private[fittizio]= private

    def get_fittizio_to_private(self):
        return self._fittizio_to_private

    def get_customers(self):
        return self._customers

    def get_pool_fittizio(self):
        return self._pool_fittizzi

    def get_name(self):
        return self._name

    def get_ip(self):
        return self._ip
    def get_public_subnet(self):
        return self._public_subnet

    def get_port(self):
        return self._port

    #Functions that have been added for DNS purposes to this class-->Habib
    def get_transaction_id(self):
        return self._transaction_id
    
    def set_transaction_id(self,t_id):
        self._transaction_id=t_id

    def get_packet_counter(self):
        return self._packet_counter

    def set_packet_counter(self,pkt_counter):
        self._packet_counter=pkt_counter

    def get_packet_ip(self):
        return self._packet_ip

    def set_packet_ip(self,pkt_ip):
        self._packet_ip=pkt_ip

    def set_port_number(self,p_number):
        self._port_number=p_number

    def get_port_number(self):
        return self._port_number

    
