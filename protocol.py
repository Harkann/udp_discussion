import socket
import logging
import threading
import dns.resolver
import struct
import time
from ipaddress import IPv6Address
from datetime import datetime, timedelta
from random import randint, sample

MAGIC_NUMBER = 93
VERSION_NUMBER = 0
ALLOWED_TYPES = [0,  # Pad1
                 1,  # PadN
                 2,  # Hello
                 3,  # Neighbour
                 4,  # Data
                 5,  # Ack
                 6,  # GoAway
                 7,  # Warning
                 ]

POT_NEIGHS = [["jch.irif.fr", 1212],
              ["2a06:e042:100:4:ebd9:fe06:9e3f:112", 7331],
              ["2a06:e042:100:c04:e0e9:d6d3:4012:5924", 7331]]
NEIGHS = {}
RECENT_DATA = {}
MY_ID = randint(0, 2**64-1)
DELAY_LHELLOS = timedelta(seconds=20)
DELAY_DISCOVERIES = timedelta(minutes=1)
DELAY_ANNOUNCE = timedelta(minutes=1)
# LAST_HELLO = datetime.today()

def resolve_add_v6(address):
    try:
        ipv6 = dns.resolver.query(address, 'AAAA')
        for rdata in ipv6:
            return rdata.address
    except:
        return address


def write_msg(tlv):
    message = (struct.pack("!B", MAGIC_NUMBER) +
               struct.pack("!B", VERSION_NUMBER) +
               struct.pack("!H", len(tlv)) +
               tlv
               )
    # print(list(message))
    return message


def write_ack(send_id, nonce):
    tlv = (struct.pack("!B", 5) +
           struct.pack("!B", 12) +
           struct.pack("!Q", send_id) +
           struct.pack("!L", nonce)
           )
    print(tlv)
    return write_msg(tlv)


def write_hello(dest_id=None):
    if dest_id is None:
        tlv = (struct.pack("!B", 2) +
               struct.pack("!B", 8) +
               struct.pack("!Q", MY_ID)
               )
    else:
        tlv = (struct.pack("!B", 2) +
               struct.pack("!B", 16) +
               struct.pack("!Q", MY_ID) +
               struct.pack("!Q", int(dest_id))
               )
    return write_msg(tlv)

def write_neighbours(dest):
    tlv = bytes()
    for n in NEIGHS:
        if n != dest:
            tlv += (struct.pack("!B", 3) +
                    struct.pack("!B", 20) +
                    struct.pack("!16s",bytes(IPv6Address(n[0]).exploded)) +
                    struct.pack("!H",n[1])
                    )
    print(list(tlv))
    return write_msg(tlv)



def send_msg(ip, rem_port, loc_port, sock, msg):
    print(list(msg))
    sock.sendto(msg, (ip, rem_port))


class Sender():
    LAST_HELLO = datetime.today()
    LAST_DISCOVERY = datetime.today()
    LAST_ANNOUNCE = datetime.today()

    def __init__(self, port, sock):
        logging.basicConfig(filename="sender.log", level=logging.DEBUG)
        logging.info("Starting sender on port : %s" % port)
        print("Starting sender on port : %s" % port)
        self.sock = sock
        self.first_hello(POT_NEIGHS)

    def first_hello(self,chosen_neighs):
        for pn in chosen_neighs:
            logging.info("S_hello sent to %s/%s" % (pn[0], pn[1]))
            print("S_hello sent to %s/%s" % (pn[0], pn[1]))
            self.sock.sendto(write_hello(), (resolve_add_v6(pn[0]), pn[1]))

    def long_hello(self):
        if datetime.today() >= DELAY_LHELLOS + self.LAST_HELLO:
            for n in NEIGHS:
                logging.info("L_hello sent to %s/%s" % (n[0], n[1]))
                print("L_hello sent to %s/%s" % (n[0], n[1]))
                self.sock.sendto(write_hello(NEIGHS[n][0]), n)
                self.LAST_HELLO = datetime.today()

    def neigh_discovery(self):
        if datetime.today() >= DELAY_DISCOVERIES + self.LAST_DISCOVERY:
            if len(NEIGHS) < 8:
                chosen = sample(POT_NEIGHS,min(8-len(NEIGHS),len(POT_NEIGHS)))
                self.first_hello(chosen)
                self.LAST_DISCOVERY = datetime.today()

    def announce_neighs(self):
        if datetime.today() >= DELAY_ANNOUNCE + self.LAST_ANNOUNCE:
            for n in NEIGHS:
                print("Neighbour sent to %s/%s" % (n[0], n[1]))
                self.sock.sendto(write_neighbours(n), n)
            self.LAST_ANNOUNCE = datetime.today()

class Receiver():
    def __init__(self, port, sock):
        logging.basicConfig(filename="receiver.log", level=logging.DEBUG)
        logging.info("Starting receiver on port : %s" % port)
        print("Starting receiver on port : %s" % port)
        self.sock = sock

    def receive_data(self):
        (data, address) = self.sock.recvfrom(1024)
        address = address[0:2]
        logging.info("Received message from %s/%s" % (address[0], address[1]))
        print("Received message from %s/%s" % (address[0], address[1]))
        self.parse_data(data, address)

    def get_tlvs(self, body, ls_tlvs):
        if body == []:
            return 0
        elif body[0] == 0:
            print("| TLV : %d" % body[0])
            tlv = [0]
            body_2 = body[1:]
            ls_tlvs.append(tlv)
        elif body[0] in ALLOWED_TYPES:
            len_tlv = body[1]
            print("| TLV : %d, Length : %s" % (body[0], len_tlv))
            tlv = body[0:len_tlv+2]
            body_2 = body[len_tlv+2:]
            ls_tlvs.append(tlv)
        else:
            print("| Dropped type %d" % body[0])
            len_tlv = body[1]
            body_2 = body[len_tlv:]
        self.get_tlvs(body_2, ls_tlvs)

    def apply_tlv(self, tlv, address):
        is_symetric = (address in NEIGHS) and (NEIGHS[address][2] is not None)
        print("| Is symetric : ", is_symetric)
        if tlv[0] == 0:
            pass
        elif tlv[0] == 1:
            pass
        elif tlv[0] == 2:
            if tlv[1] == 8:
                source_id = struct.unpack("!Q", bytes(tlv[2:]))[0]
                print("| S_hello received from id : %d" % source_id)
                if address in NEIGHS.keys():
                    NEIGHS.update({address: [source_id,
                                             datetime.today(),
                                             NEIGHS[address][2]
                                             ]
                                   })
                else:
                    NEIGHS.update({address: [source_id,
                                             datetime.today(),
                                             None
                                             ]
                                   })
                self.sock.sendto(write_hello(source_id), address)
            elif tlv[1] == 16:
                source_id = struct.unpack("!Q", bytes(tlv[2:10]))[0]
                dest_id = struct.unpack("!Q", bytes(tlv[10:]))[0]
                # print(dest_id)
                if dest_id != MY_ID:
                    print("| Not for me")
                    return 1
                print("| L_hello received from id : %d" % source_id)
                NEIGHS.update({address: [source_id,
                                         datetime.today(),
                                         datetime.today()
                                         ]
                               })
            else:
                pass
        elif tlv[0] == 3:
            len_tlv = tlv[1]
            ip = struct.unpack("!16s",bytes(tlv[2:18]))[0]
            ip = IPv6Address(ip).exploded
            port = struct.unpack("!H",bytes(tlv[18:len_tlv+2]))[0]
            print("| New potential neighbour at %s/%d" % (ip,
                                                          port
                                                          ))
            if [ip,port]not in POT_NEIGHS:
                POT_NEIGHS.append([ip,port])
        elif tlv[0] == 4:
            len_tlv = tlv[1]
            source_id = struct.unpack("!Q", bytes(tlv[2:10]))[0]
            nonce = struct.unpack("!L", bytes(tlv[10:14]))[0]
            data = bytes(tlv[14:len_tlv+2])
            print("Data received from id %d" % source_id)
            print("Message : " + str(data))
            self.sock.sendto(write_ack(source_id, nonce), address)
        elif tlv[0] == 5:
            pass
        elif tlv[0] == 6:
            len_tlv = tlv[1]
            code = tlv[2]
            message = bytes(tlv[3:len_tlv])
            print("| GoAway with code %d from" % code, address, "with message :", message)
            if address in NEIGHS.keys():
                NEIGHS.pop(address)
        elif tlv[0] == 7:
            len_tlv = tlv[1]
            data = bytes(tlv[2:len_tlv+2])
            print("| Warning : " + str(data))
        else:
            pass

    def parse_data(self, data, address):
        ls_data = list(data)

        if ls_data[0] != MAGIC_NUMBER:
            print("Wrong magic number")
            return 1
        elif ls_data[1] != VERSION_NUMBER:
            print("Wrong version number")
            return 1
        body_len = struct.unpack("!H", bytes(ls_data[2:4]))[0]
        print("| Message length : %d" % body_len)
        if len(ls_data) > body_len + 4:
            print("Datagram too large")
            return 1
        body = ls_data[4:]
        ls_tlvs = []
        self.get_tlvs(body, ls_tlvs)
        for tlv in ls_tlvs:
            self.apply_tlv(tlv, address)

class Interface():
    def __init__(self):
        pass

class Receiver_thread(threading.Thread):
    def __init__(self, port, sock):
        threading.Thread.__init__(self)
        self.receiver = Receiver(port,
                                 sock
                                 )

    def run(self):
        while True:
            self.receiver.receive_data()


class Sender_thread(threading.Thread):
    def __init__(self, port, sock):
        threading.Thread.__init__(self)
        self.sender = Sender(port,
                             sock
                             )

    def run(self):
        while True:
            time.sleep(5)
            print(NEIGHS)
            self.sender.long_hello()
            self.sender.neigh_discovery()
            try:
                self.sender.announce_neighs()
            except:
                print("TODO : fix announce")

class Interface_Thread(threading.Thread):
    pass

class Client():
    def __init__(self, port, protocol=socket.AF_INET6, interface="CLI"):
        sock = socket.socket(protocol, socket.SOCK_DGRAM)
        sock.bind(("", port))

        self.receiver = Receiver_thread(port, sock)
        self.sender = Sender_thread(port, sock)

        self.receiver.daemon = True
        self.sender.daemon = True

    def start(self):
        self.receiver.start()
        self.sender.start()

        self.receiver.join()
        self.sender.join()
