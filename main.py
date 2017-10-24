import socket
import struct
import protocol
"""
host = 'www.freebsd.org'

answers_IPv4 = dns.resolver.query(host, 'A')
for rdata in answers_IPv4:
    print('IPv4:', rdata.address)

answers_IPv6 = dns.resolver.query(host, 'AAAA')
for rdata in answers_IPv6:
    print('IPv6:', rdata.address)
"""
"""
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MESSAGE = "Hello, World!"
print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT)
print("message:", MESSAGE)
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
"""
body = b"0"
message = b"%s%s%s%s", str(hex(93)), str(hex(0)), hex(len(body)), body

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


def format_msg(tlvs):
    message = b"%s%s", str(hex(93)), str(hex(0))
    body = b""
    for tlv in tlvs:
        body += tlv
    message += str(hex(len(body))) + body
    return message


def send_message(sock, message, ip, port):
    try:
        sock.sendto(message, (ip, port))
    except:
        pass

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sock.bind(("", 1337))


receiver = protocol.Receiver_thread(1337,
                                    sock
                                    )

sender = protocol.Sender_thread(1337,
                                sock
                                )
receiver.daemon = True
sender.daemon = True
receiver.start()
sender.start()
receiver.join()
sender.join()
