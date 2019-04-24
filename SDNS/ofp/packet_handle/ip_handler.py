from netaddr import *
from ryu.lib.packet import ipv4
from ryu.ofproto import ether
from ryu.ofproto.ofproto_v1_3 import OFP_NO_BUFFER

from packet_handler import PacketHandler

__author__ = 'robertodilallo'

from utils.communication import Client
from utils.connection import Connection


class IpHandler(PacketHandler):
    def __init__(self, pkt, dp_to_customer, in_port, data, datapath, controller, federazione, public_to_private_a,
                 public_to_private_b):
        PacketHandler.__init__(self, pkt)
        self._pkt = pkt
        self._dp_to_customer = dp_to_customer
        self._federazione = federazione
        self._controller = controller
        self._in_port = in_port
        self._datapath = datapath
        self._data = data
        self._public_to_private_a = public_to_private_a
        self._public_to_private_b = public_to_private_b
        self._public_address_src = None
        self._public_address_dst = None


    def handle_packet(self):

        # Divido la gestione dei pacchetti dalla porta di ingresso dello switch
        # e dalla tipologia del pacchetto VPN o Ip pubblico

        if self._in_port != 1 and IPAddress(
                self._pkt.get_protocol(ipv4.ipv4).dst).is_private() and not IPAddress(self._pkt.get_protocol(
                ipv4.ipv4).src).is_private():
            self.from_df_gw(self._pkt)

        elif self._in_port != 1 and IPAddress(self._pkt.get_protocol(ipv4.ipv4).dst).is_private():

            self.from_cs_to_private(self._pkt)

        elif self._in_port != 1 and not IPAddress(self._pkt.get_protocol(ipv4.ipv4).dst).is_private():
            self.from_cs_to_public(self._pkt)

        if self._in_port == 1 and self._pkt.get_protocol(ipv4.ipv4).src in self._public_to_private_b.keys():

            self.to_cs_from_private(self._pkt)

        elif self._in_port == 1 and self._pkt.get_protocol(ipv4.ipv4).src not in self._public_to_private_b.keys():
            print "risposta da :", self._pkt.get_protocol(ipv4.ipv4).src
            self.to_cs_from_public(self._pkt)

    def from_cs_to_private(self, pkt):

        private_address_src = pkt.get_protocol(ipv4.ipv4).src
        ip_dst = pkt.get_protocol(ipv4.ipv4).dst

        # Verifico se la destinazione e^ un ip fittizio (indirizzamento sovrapposto)
        if ip_dst in self._controller.get_fittizio_to_private().keys():
            private_address_dst = self._controller.get_fittizio_to_private()[ip_dst]
        else:
            private_address_dst = ip_dst

        # Verifico se ho gia^ un mapping (pubblico<-->privato) per l'ip del MIO customer
        if private_address_src in self._public_to_private_a.values():

            for public, private in self._public_to_private_a.items():
                if private_address_src == private:
                    self._public_address_src = public
        else:

            ip_iterator_src = self._controller.get_public_subnet().iter_hosts()
            self._public_address_src = ip_iterator_src.next().__str__()

            # Genero un ip non in uso dal "MIO" pool per la sorgente.
            while self._public_address_src in self._public_to_private_a.keys():
                self._public_address_src = ip_iterator_src.next().__str__()

            self._public_to_private_a[self._public_address_src] = private_address_src
            # Aggiungo una rotta statica per il ip pubblico scelto per gestire il traffico di ritorno
            customer = self._dp_to_customer[self._datapath.id, str(self._in_port)]
            connection = Connection()
            connection.addStaticRoute(customer.get_router(),
                                      "sudo route add -host " + self._public_address_src + " gw " + customer.get_next_hop() + " dev eth2",
                                      self._public_address_src)




        # Verifico se ho gia^ un mapping (pubblico<-->privato) per l'ip del customer federato
        if private_address_dst in self._public_to_private_b.values():
            for public1, private1 in self._public_to_private_b.items():
                if private_address_dst == private1:
                    self._public_address_dst = public1

        else:
            # Devo individuare da quale federato (pool) devo prendere un ip per la destinazione.
            # Con l'implementazione della risoluzione dei nomi il controller sa individuare il federato a partitre dal nome.
            # Per ora so che esiste un solo federato con cui ho instaurato delle VPN ed utilizzo lui

            ip_iterator_dst = self._federazione[0].get_public_subnet().iter_hosts()
            self._public_address_dst = ip_iterator_dst.next().__str__()

            # Genero un ip non in uso dal pool di c2 per la destinazione
            while self._public_address_dst in self._public_to_private_b.keys():
                self._public_address_dst = ip_iterator_dst.next().__str__()

            self._public_to_private_b[self._public_address_dst] = private_address_dst

            # Segnalo l'associazio pubblico<-->privato
            client = Client()
            client.send_message(
                    "binding;src:" + private_address_src + ":" + self._public_address_src + ",dst:" + private_address_dst + ":" + self._public_address_dst,
                    self._federazione[0].get_ip(),
                    self._federazione[0].get_port())

       # print "from_cs_to_private dst :", ip_dst, " src: ", private_address_src





        ofp = self._datapath.ofproto
        parser = self._datapath.ofproto_parser
        actions = [
            parser.OFPActionSetField(ipv4_src=self._public_address_src),
            parser.OFPActionSetField(ipv4_dst=self._public_address_dst),
            parser.OFPActionOutput(1)]
        out = parser.OFPPacketOut(datapath=self._datapath, data=self._data, in_port=self._in_port, actions=actions,
                                  buffer_id=OFP_NO_BUFFER)
        self._datapath.send_msg(out)

        #Inserisco un flow-entry per i pacchetti in uscita
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ipv4_src=private_address_src,
                                ipv4_dst=ip_dst)
        actions = [
            parser.OFPActionSetField(ipv4_src=self._public_address_src),
            parser.OFPActionSetField(ipv4_dst=self._public_address_dst),
            parser.OFPActionOutput(1)
        ]
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=self._datapath, match=match, instructions=inst, priority=1)
        self._datapath.send_msg(mod)

        # Inserisco una flow-entry per i pacchetti in entrata

        # Verifico la porta di uscita del datapath in funzione della subnet privata dei miei customer
        # Assunzione: customer sotto lo stesso datapath devono avere subnet private differenti

        for customer in self._controller.get_customers():
            if customer.get_datapath() == self._datapath and customer.get_private_ip_subnet().__contains__(
                    IPAddress(private_address_src)):
                out_port = int(customer.get_ingress_port())
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ipv4_dst=self._public_address_src,
                                ipv4_src=self._public_address_dst)
        actions = [
            parser.OFPActionSetField(ipv4_src=ip_dst),
            parser.OFPActionSetField(ipv4_dst=private_address_src),
            parser.OFPActionOutput(out_port)
        ]
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=self._datapath, match=match, instructions=inst, priority=1)
        self._datapath.send_msg(mod)

    def to_cs_from_private(self, pkt):

        public_address_dst = pkt.get_protocol(ipv4.ipv4).dst
        public_address_src = pkt.get_protocol(ipv4.ipv4).src

        private_address_dst = self._public_to_private_a[public_address_dst]
        private_address_src = self._public_to_private_b[public_address_src]

        if private_address_src == private_address_dst:
            for fittizio, private in self._controller.get_fittizio_to_private().items():
                if private == private_address_src:
                    private_address_src = fittizio

        for customer in self._controller.get_customers():
            if customer.get_datapath() == self._datapath and customer.get_private_ip_subnet().__contains__(
                    IPAddress(private_address_dst)):
                out_port = int(customer.get_ingress_port())

        ofp = self._datapath.ofproto
        parser = self._datapath.ofproto_parser

        actions = [
            parser.OFPActionSetField(ipv4_src=private_address_src),
            parser.OFPActionSetField(ipv4_dst=private_address_dst),
            parser.OFPActionOutput(out_port)
        ]
        out = parser.OFPPacketOut(datapath=self._datapath, data=self._data, in_port=self._in_port, actions=actions,
                                  buffer_id=OFP_NO_BUFFER)
        self._datapath.send_msg(out)

    def from_cs_to_public(self, pkt):
        private_address_src = pkt.get_protocol(ipv4.ipv4).src

        if private_address_src in self._public_to_private_a.values():

            for public, private in self._public_to_private_a.items():
                if private_address_src == private:
                    self._public_address_src = public
        else:

            ip_iterator_src = self._controller.get_public_subnet().iter_hosts()
            self._public_address_src = ip_iterator_src.next().__str__()

            # Genero un ip non in uso dal "MIO" pool per la sorgente.    DA VERIFICARE IL PUNTATORE SU IP_ITERATOR!!!!
            while self._public_address_src in self._public_to_private_a.keys():
                self._public_address_src = ip_iterator_src.next().__str__()

            self._public_to_private_a[self._public_address_src] = private_address_src
            customer = self._dp_to_customer[self._datapath.id, str(self._in_port)]
            connection = Connection()
            connection.addStaticRoute(customer.get_router(),
                                      "sudo route add -host " + self._public_address_src + " gw " + customer.get_next_hop() + " dev eth2",
                                      self._public_address_src)

        ofp = self._datapath.ofproto
        parser = self._datapath.ofproto_parser
        actions = [
            parser.OFPActionSetField(ipv4_src=self._public_address_src),
            parser.OFPActionOutput(1)]
        out = parser.OFPPacketOut(datapath=self._datapath, data=self._data, in_port=self._in_port, actions=actions,
                                  buffer_id=OFP_NO_BUFFER)
        self._datapath.send_msg(out)

    def from_df_gw(self, pkt):
        ip_dst = pkt.get_protocol(ipv4.ipv4).dst

        if ip_dst in self._controller.get_fittizio_to_private().keys():
            private_address_dst = self._controller.get_fittizio_to_private()[ip_dst]
        else:
            private_address_dst = ip_dst

        for public, private in self._public_to_private_b.items():
            if private_address_dst == private:
                self._public_address_dst = public

        ofp = self._datapath.ofproto
        parser = self._datapath.ofproto_parser
        actions = [
            parser.OFPActionSetField(ipv4_dst=self._public_address_dst),
            parser.OFPActionOutput(1)]
        out = parser.OFPPacketOut(datapath=self._datapath, data=self._data, in_port=self._in_port, actions=actions,
                                  buffer_id=OFP_NO_BUFFER)
        self._datapath.send_msg(out)

    def to_cs_from_public(self, pkt):


        public_address_dst = pkt.get_protocol(ipv4.ipv4).dst
        private_address_dst = self._public_to_private_a[public_address_dst]
        
        print "dst :", private_address_dst
        for customer in self._controller.get_customers():
            if customer.get_datapath() == self._datapath and customer.get_private_ip_subnet().__contains__(
                    IPAddress(private_address_dst)):
                out_port = int(customer.get_ingress_port())

        ofp = self._datapath.ofproto
        parser = self._datapath.ofproto_parser

        actions = [
            parser.OFPActionSetField(ipv4_dst=private_address_dst),
            parser.OFPActionOutput(out_port)
        ]
        out = parser.OFPPacketOut(datapath=self._datapath, data=self._data, in_port=self._in_port, actions=actions,
                                  buffer_id=OFP_NO_BUFFER)

        self._datapath.send_msg(out)

    def request_stats(self, datapath):
        print 'send stats request: %016x', datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)
