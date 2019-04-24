__author__ = 'robertodilallo'

from logging import Logger

from abc import ABCMeta, abstractmethod

class absnat(object):

    __metaclass__ = ABCMeta

    #def __init__(self):
        #The logger
        #self._log = Logger.get_instance()


    @abstractmethod
    def get_binding_ce1a(self):
        pass

    @abstractmethod
    def get_binding_ce1b(self):
        pass

    @abstractmethod
    def get_private_ce1a(self):
        pass

    @abstractmethod
    def get_private_ce1b(self):
        pass