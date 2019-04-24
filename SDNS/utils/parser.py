__author__ = 'gab'

import ConfigParser

from model.node import Controller
from model.customer import Customer, CustomerAlg1


class Parser(object):
    def __init__(self, listen_port):
        self._config = ConfigParser.ConfigParser()
        # The controllers in the configuration file
        self._federazione = []
        self._customers = []
        self._controller = None
        # The association between each customer and the datapath. It will be used for setting
        # the ryu.controller.Datapath instance when Ryu will detect that datapath.

        # This values is used for avoiding to store the information about this controller
        # Being all controllers on localhost, I can use only one (shared) configuration.
        self._listen_port = listen_port

    #    self._datapaths={}   #chiave: id datapath valore: Datapath model.node

    def get_federazione(self):
        return self._federazione

    def get_controller(self):
        return  self._controller

    def get_customers(self):
        return self._customers


    def load(self, config_file):
        # Load the configuration file
        self._config.readfp(open(config_file))
        # Load controllers; each controller has to connect to each other in order to create
        # a virtual track.
        federazione = self._config.items('Federazione')
        for controller in federazione:
            c_name = controller[0]
            c_ip, public_pool = controller[1].split(',')
            c_port = self._listen_port
            c = Controller(c_name, c_ip, c_port, public_pool)
            # Add the new controller to the list of controllers
            self._federazione.append(c)
            # For this controller, load all customer
        isp = self._config.items("Controller")
        for provider in isp:
            name = provider[0]
            ip,pub,fitt = provider[1].split(',')
            self._controller = Controller (name, ip, self._listen_port ,pub)
            self._controller.set_pool_fittizzi(fitt)
            self._controller.set_fittizio("192.168.1.1","10.1.0.1")
            self._load_customers(self._controller)

    # Load customers for controller identified by controller_name
    def _load_customers(self, controller):
        customers = self._config.items("Customers")
        
        for customer in customers:
            citems=customer[1].split(',')
            if len(citems)>7:
                customer_name = customer[0]
                (private_ip_subnet, ingress_interface, ip_datapath,router,next_hop, name_server,out_port,datapath_to_router_ip,datapath_to_router_interface,ns_domain_name) = citems
                c = Customer(customer_name, private_ip_subnet, ingress_interface, ip_datapath,router,next_hop,out_port,datapath_to_router_ip,datapath_to_router_interface,ns_domain_name)
                if name_server != "":
                    print name_server + "NS"
                    c.set_name_server(name_server)
            else:
                customer_name = customer[0]
                (private_ip_subnet, ingress_interface, ip_datapath,router,next_hop, name_server) = citems
                c = CustomerAlg1(customer_name, private_ip_subnet, ingress_interface, ip_datapath,router,next_hop)
                if name_server != "":
                    print name_server + "NS"
                    c.set_name_server(name_server)
            
            self._customers.append(c)
            controller.set_customers(c)


    def print_results(self):
        print 'Parser results.'
        print ' - Controllers: %s' % self._controllers
        print ' - Customers: %s' % self._customers
        print ' - Customer -> CE: %s' % self._dp_to_customer
