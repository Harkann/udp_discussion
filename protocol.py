import socket
import logging
import threading
import dns.resolver
import struct
import time
from datetime import datetime, timedelta
from random import randint

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
MY_ID = randint(0, 2**64-1)
DELAY_LHELLOS = timedelta(seconds=20)
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
    tlv = (struct.pack("!B", 4) +
           struct.pack("!B", 12) +
           struct.pack("!Q", send_id) +
           struct.pack("!L", nonce)
           )
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
               struct.pack("!Q", dest_id)
               )
    return write_msg(tlv)


def send_msg(ip, rem_port, loc_port, sock, msg):
    print(list(msg))
    sock.sendto(msg, (ip, rem_port))


class Sender():
    LAST_HELLO = datetime.today()

    def __init__(self, port, sock):
        logging.basicConfig(filename="sender.log", level=logging.DEBUG)
        logging.info("Starting sender on port : %s" % port)
        print("Starting sender on port : %s" % port)
        self.sock = sock
        self.first_hello()

    def first_hello(self):
        for pn in POT_NEIGHS:
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
            print("TLV : %d" % body[0])
            tlv = [0]
            body_2 = body[1:]
            ls_tlvs.append(tlv)
        elif body[0] in ALLOWED_TYPES:
            len_tlv = body[1]
            print("TLV : %d, Length : %s" % (body[0], len_tlv))
            tlv = body[0:len_tlv+2]
            body_2 = body[len_tlv+2:]
            ls_tlvs.append(tlv)
        else:
            print("Dropped type %d" % body[0])
            len_tlv = body[1]
            body_2 = body[len_tlv:]
        self.get_tlvs(body_2, ls_tlvs)

    def apply_tlv(self, tlv, address):
        if tlv[0] == 0:
            pass
        elif tlv[0] == 1:
            pass
        elif tlv[0] == 2:
            if tlv[1] == 8:
                source_id = struct.unpack("!Q", bytes(tlv[2:]))
                print("S_hello received from id : %d" % source_id)
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
                    print("Not for me")
                    return 1
                print("L_hello received from id : %d" % source_id)
                NEIGHS.update({address: [source_id,
                                         datetime.today(),
                                         datetime.today()
                                         ]
                               })
            else:
                pass
        elif tlv[0] == 3:
            pass
        elif tlv[0] == 4:
            len_tlv = tlv[1]
            source_id = struct.unpack("!Q", bytes(tlv[2:10]))[0]
            nonce = struct.unpack("!L", bytes(tlv[10:16]))[0]
            data = bytes(tlv[16:len_tlv+2])
            print("Data received from id %d" % source_id)
            print("Message : " + data)
            print(data)
            self.sock.sendto(write_ack(source_id, nonce), address)
        elif tlv[0] == 5:
            pass
        elif tlv[0] == 6:
            pass
        elif tlv[0] == 7:
            pass
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
        print("Message length : %d" % body_len)
        if len(ls_data) > body_len + 4:
            print("Datagram too large")
            return 1
        body = ls_data[4:]
        ls_tlvs = []
        self.get_tlvs(body, ls_tlvs)
        for tlv in ls_tlvs:
            self.apply_tlv(tlv, address)


class Receiver_thread(threading.Thread):
    def __init__(self, port, sock):
        threading.Thread.__init__(self)
        self.receiver = Receiver(port,
                                 sock
                                 )

    def run(self):
        while True:
            time.sleep(5)
            self.receiver.receive_data()


class Sender_thread(threading.Thread):
    def __init__(self, port, sock):
        threading.Thread.__init__(self)
        self.sender = Sender(port,
                             sock
                             )

    def run(self):
        while True:
            self.sender.long_hello()
