
import hashlib
import struct


class Packet :
    HEADERFORMAT = "!IB16s"

    def __init__(self , seq ,packet_type , payload):
        self.__seq = seq
        self.__packet_type = packet_type
        self.__payload = payload if payload is not None else b''
        self.__checksum = hashlib.md5(self.__payload).digest()

    def to_bytes(self):
        return struct.pack(self.HEADERFORMAT, self.__seq , self.__packet_type, self.__checksum) + self.__payload
    
    @staticmethod
    def header_size():
        return struct.calcsize(Packet.HEADERFORMAT)

    @staticmethod
    def from_byte(raw_byte):
        header_size = struct.calcsize(Packet.HEADERFORMAT)
        header = raw_byte[:header_size]
        payload = raw_byte[header_size:]

        seq , packet_type , checksum = struct.unpack(Packet.HEADERFORMAT, header)
        return  seq , packet_type , checksum ,payload
    
    @property
    def seq(self):
        return self.__seq
    
    @property
    def packet(self):
        return self.__packet_type
    
    @property
    def payload(self):
        return self.__payload
    
    @property
    def checksum(self):
        return self.__checksum
    
    