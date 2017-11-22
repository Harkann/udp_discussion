import struct
import dns
from ipaddress import IPv6Address

def resolve_add_v6(address):
    try:
        ipv6 = dns.resolver.query(address, 'AAAA')
        for rdata in ipv6:
            return rdata.address
    except:
        return address


def write_msg(magic_number, version_number, tlv):
    struct.pack("!H", len(tlv))
    message = (
        struct.pack("!B", magic_number) +
        struct.pack("!B", version_number) +
        struct.pack("!H", len(tlv)) +
        tlv
    )
    return message


def format_message(magic_number, version_number, list_mes):
    if list_mes[0] == "Pad1":
        pass
    elif list_mes[0] == "PadN":
        pass
    elif list_mes[0] == "Hello":
        if list_mes[2] is None:
            message = write_msg(
                magic_number,
                version_number,
                struct.pack("!B", 2) +
                struct.pack("!B", 8) +
                struct.pack("!Q", list_mes[1])  # my id
            )
        else:
            message = write_msg(
                magic_number,
                version_number,
                struct.pack("!B", 2) +
                struct.pack("!B", 16) +
                struct.pack("!Q", list_mes[1]) +  # my id
                struct.pack("!Q", list_mes[2])    # dest id
            )
    elif list_mes[0] == "Neighbour":
        tlv = bytes()
        tlv = (
            struct.pack("!B", 3) +
            struct.pack("!B", 20) +
            struct.pack("!16s", bytes(IPv6Address(list_mes[1][0]).exploded.encode("utf-8"))) +
            struct.pack("!H", list_mes[1][1])
        )
        message = write_msg(
            magic_number,
            version_number,
            tlv
        )
    elif list_mes[0] == "Data":
        message = write_msg(
            magic_number,
            version_number,
            struct.pack("!B", 4) +
            struct.pack("!B", len(list_mes[1]) + 8 + 4) +
            struct.pack("!Q", MY_ID) +
            struct.pack("!L",nonce) +
            struct.pack("!%ds" % len(list_mes[2]), bytes(list_mes[2].encode("utf-8")))
        )
    elif list_mes[0] == "Ack":
        message = write_msg(
            magic_number,
            version_number,
            struct.pack("!B", 5) +
            struct.pack("!B", 12) +
            struct.pack("!Q", list_mes[1]) + # send_id
            struct.pack("!L", list_mes[2])   # nonce
        )
    elif list_mes[0] == "GoAway":
        message = write_msg(
            magic_number,
            version_number,
            struct.pack("!B", 6) +
            struct.pack("!B", 1 + len(list_mes[2])) +
            struct.pack("!B", list_mes[1]) +
            struct.pack("!%ds" % len(list_mes[2]), bytes(list_mes[2].encode("utf-8")))
        )
    elif list_mes[0] == "Warning":
        pass
    else:
        return -1
    return message
