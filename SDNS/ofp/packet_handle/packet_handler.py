__author__ = 'robertodilallo'

from abc import ABCMeta, abstractmethod

class PacketHandler(object):

    __metaclass__ = ABCMeta

    def __init__(self,pkt):
        self._pkt = pkt


    @abstractmethod
    def handle_packet(self):
        pass

