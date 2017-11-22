import struct
from ipaddress import IPv6Address
from datetime import datetime
import tkinter as tk

def get_tlvs(body, ls_tlvs, client):
    """
        Retourne la liste des tlvs composant le message
    """
    # Tout le body a été parsé
    if body == []:
        return 0
    # Si le tlv est un Pad1
    elif body[0] == 0:
        tlv = [0]
        body_2 = body[1:]
        ls_tlvs.append(tlv)
    # Si le TLV est dans la liste des TLVs connus
    elif body[0] in client.ALLOWED_TYPES.keys():
        len_tlv = body[1]
        tlv = body[0:len_tlv+2]
        body_2 = body[len_tlv+2:]
        ls_tlvs.append(tlv)
    # Sinon on le drop
    else:
        len_tlv = body[1]
        body_2 = body[len_tlv:]
    # Et on fait ça récursivement
    get_tlvs(body_2, ls_tlvs, client)


def parse_data(data, address, client):
    """
    Parse le paquet et applique les effets des différents tlvs
    """
    ls_data = list(data)

    # Checke le magic number
    if ls_data[0] != client.MAGIC_NUMBER:
        return 1

    # Checke le numéro de version
    elif ls_data[1] != client.VERSION_NUMBER:
        return 1

    # Vérifie le respect de la longueur du body
    body_len = struct.unpack("!H", bytes(ls_data[2:4]))[0]
    if len(ls_data) > body_len + 4:
        return 1

    # découpe le message comme il faut
    body = ls_data[4:]
    ls_tlvs = []
    get_tlvs(body, ls_tlvs, client)
    for tlv in ls_tlvs:
        # pass
        apply_tlv(tlv, address, client)


def apply_tlv(tlv, address, client):
    client.interface.add_log("[RECV]: {} from {}".format(client.ALLOWED_TYPES[tlv[0]], address), "received")
    is_symetric = (
        (client.NEIGHS.get(address) is not None) and
        (client.NEIGHS.get(address).get("is_symetric") is not None)
    )
    # Pad1
    if tlv[0] == 0:
        pass
    # PadN
    elif tlv[0] == 1:
        pass
    # Hello
    elif tlv[0] == 2:
        # Si c'est un short hello
        if tlv[1] == 8:
            source_id = struct.unpack("!Q", bytes(tlv[2:]))[0]
            # On vérifie qu'on s'ajoute pas soi même comme voisin
            if source_id == client.MY_ID:
                return 1
            # On connait déja le client, on update last hello et c'est tout
            if address in client.NEIGHS.keys():
                client.NEIGHS.update(
                    {
                        address: {
                            "id": source_id,
                            "is_symetric": False,
                            "last_long": client.NEIGHS[address]["last_long"],
                            "last": datetime.today()
                        }
                    }
                )
            # On ne connait pas encore le client,
            # on update last hello et on lui envoie un long hello
            else:
                client.NEIGHS.update(
                    {
                        address: {
                            "id": source_id,
                            "is_symetric": False,
                            "last_long": None,
                            "last": datetime.today()
                        }
                    }
                )
                message = client.format_message([
                    "Hello",
                    client.MY_ID,
                    source_id
                ])
                client.send_message(message, address)

        # Si c'est un long hello
        elif tlv[1] == 16:
            source_id = struct.unpack("!Q", bytes(tlv[2:10]))[0]
            dest_id = struct.unpack("!Q", bytes(tlv[10:]))[0]
            # Il n'est pas pour moi
            if dest_id != client.MY_ID:
                return 1
            # Si il était pas symétrique avant on lui envoie un long hello
            if not is_symetric:
                message = client.format_message([
                    "Hello",
                    client.MY_ID,
                    source_id
                ])
                client.send_message(message, address)
            # On met à jour la base des voisins et on le considère comme symétrique
            client.NEIGHS.update(
                {
                    address: {
                        "id": source_id,
                        "is_symetric": True,
                        "last_long": datetime.today(),
                        "last": datetime.today()
                    }
                }
            )
        # TLV pas de dimension standard, on pourrait envoyer un Warning
        else:
            pass
        client.interface.update_neighs()
    # Neighbour
    elif tlv[0] == 3:
        len_tlv = tlv[1]
        ip = struct.unpack("!16s", bytes(tlv[2:18]))[0]
        drop = False
        # On vérifie que c'est bien une ipv6 et pas une ipv4
        if IPv6Address(ip).ipv4_mapped is None:
            ip = IPv6Address(ip).exploded
        # Sinon on la drope
        else:
            ip = IPv6Address(ip).ipv4_mapped
            drop = True
        # On récupère le port
        port = struct.unpack("!H", bytes(tlv[18:len_tlv+2]))[0]
        # On l'ajoute dans les voisins potentiels si c'est une v6
        if (ip, port) not in client.POT_NEIGHS and not drop:
            client.POT_NEIGHS.append((ip, port))
        client.interface.update_neighs()
    # Data
    elif tlv[0] == 4:
        len_tlv = tlv[1]
        source_id = struct.unpack("!Q", bytes(tlv[2:10]))[0]
        nonce = struct.unpack("!L", bytes(tlv[10:14]))[0]
        data = bytes(tlv[14:len_tlv+2]).decode("utf-8")
        client.add_to_recent(source_id, nonce, data)
        # et envoyer un ack
        message = client.format_message([
            "Ack",
            source_id,
            nonce
        ])
        client.send_message(message, address)

    # Ack
    elif tlv[0] == 5:
        len_tlv = tlv[1]
        source_id = struct.unpack("!Q", bytes(tlv[2:10]))[0]
        nonce = struct.unpack("!L", bytes(tlv[10:14]))[0]
        if (source_id, nonce) in client.RECENT_DATA.keys():
            client.RECENT_DATA.pop((source_id, nonce))

    # GoAway
    elif tlv[0] == 6:

        len_tlv = tlv[1]
        code = tlv[2]
        message = bytes(tlv[3:len_tlv+2])
        if address in client.NEIGHS.keys():
            client.NEIGHS.pop(address)
            client.POT_NEIGHS.append(address)
        client.interface.update_neighs()
        client.interface.insert_text(
            "[ERROR]: GoAway from {} with code {}, message : {}".format(
                address,
                code,
                message
            ).encode("utf-8"),
            "error"
        )

    # Warning
    elif tlv[0] == 7:
        len_tlv = tlv[1]
        data = bytes(tlv[2:len_tlv+2])
    else:
        pass
