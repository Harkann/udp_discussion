import socket
import struct
import protocol


pot_neighbours = [["jch.irif.fr", 1212],
                  ["2a06:e042:100:4:ebd9:fe06:9e3f:112", 7331],
                  ["2a06:e042:100:c04:e0e9:d6d3:4012:5924", 7331]]
neighbours = {}  # format : (ip,port) : [id,date_last_h,date_last_long_h]


def resolve_add_v4(address):
    try:
        ipv4 = dns.resolver.query(address, 'A')
        for rdata in ipv4:
            return rdata.address
    except:
        return address

client = protocol.Client(1337)
client.start()
