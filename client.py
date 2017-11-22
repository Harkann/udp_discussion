import socket
from interface import Interface
from tools import resolve_add_v6, format_message, write_msg
from random import randint, sample
from datetime import datetime, timedelta
from parser import parse_data
import copy
import time
import struct
from threading import Thread, Event
import config as cfg

class Client():
    def __init__(self):
        self.MAGIC_NUMBER = cfg.MAGIC_NUMBER
        self.VERSION_NUMBER = cfg.VERSION_NUMBER
        self.PORT = cfg.PORT
        self.ALLOWED_TYPES = cfg.ALLOWED_TYPES
        self.DELAY_LHELLOS = timedelta(seconds=cfg.DELAY_LHELLOS)
        self.DELAY_DISCOVERIES = timedelta(seconds=cfg.DELAY_DISCOVERIES)
        self.DELAY_ANNOUNCE = timedelta(seconds=cfg.DELAY_ANNOUNCE)
        self.NICK = cfg.NICK
        self.DEFAULT_POT = cfg.DEFAULT_POT
        self.POT_NEIGHS = self.DEFAULT_POT
        self.NEIGHS = dict()
        # (address, port): {id: id, is_symetric: False, last_long: time, last: time}
        self.RECENT_DATA = dict()
        self.MY_ID = randint(0, 2**64-1)
        self.LAST_HELLO = datetime.today()
        self.LAST_DISCOVERY = datetime.today()
        self.LAST_ANNOUNCE = datetime.today()
        self.MIN_NEIGHS = 8
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.bind(("", self.PORT))
        self.running = Event()

        self.interface = Interface(self)

        for n in self.DEFAULT_POT:
            self.connect(n)

        self.receive_thread = Thread(target=self.receive)
        self.routine_thread = Thread(target=self.routine)
        self.dispatch_thread = Thread(target=self.dispatch)
        self.receive_thread.start()
        self.routine_thread.start()
        self.dispatch_thread.start()
        self.interface.root.protocol("WM_DELETE_WINDOW", self.interface.on_closing)
        self.interface.root.mainloop()
        self.receive_thread.join()
        self.routine_thread.join()
        self.dispatch_thread.join()

    def kill_all(self):
        """
        Ferme le programme
        """
        neighbours = copy.deepcopy(self.NEIGHS)
        for vois in neighbours:
            self.send_goaway(vois, 1)
        self.running.set()

    def send_goaway(self, voisin, code, reason=None):
        """
        Envoie un Goaway
        """
        reason = ""
        if voisin in self.NEIGHS:
            if code == 1:
                reason = "Disconnect"
                tlv = [
                    "GoAway",
                    1,
                    reason
                ]
            elif code == 2:
                if reason is None:
                    reason = "Too slow"
                tlv = [
                    "GoAway",
                    2,
                    reason
                ]
            else :
                pass
            message = self.format_message(tlv)
            self.send_message(message, voisin)
            self.NEIGHS.pop(voisin)
            self.interface.update_neighs()

    def add_to_recent(self, source_id, nonce, message):
        """
        Ajoute dans la liste des messages récement envoyés ou reçus
        """
        if (source_id, nonce) not in self.interface.RECENT_DISPLAY:
            self.interface.RECENT_DISPLAY.append((source_id, nonce))
            tlv = (
                struct.pack("!B", 4) +
                struct.pack("!B", len(message.encode("utf-8")) + 8 + 4) +
                struct.pack("!Q", source_id) +
                struct.pack("!L", nonce) +
                struct.pack("!{}s".format(len(list(message.encode("utf-8")))), bytes(message.encode("utf-8")))
            )
            send_to = dict()
            for key in self.NEIGHS.keys():
                if self.NEIGHS[key]["id"] != source_id:
                    send_to.update(
                        {
                            key: {
                                "last_try": None,
                                "trys_left": 5
                            }
                        }
                    )
            if send_to != {}:
                self.RECENT_DATA.update(
                    {
                        (source_id, nonce): {
                            "dests": send_to,
                            "tlv": tlv
                        }
                    }
                )
            self.interface.insert_text(message)

    def send_message(self, message, destination):
        """
        Envoie un message
        """
        self.interface.add_log("[SEND]: {} to {}".format(list(message), destination), "send")
        try:
            self.sock.sendto(message, destination)
            self.interface.update_status(True)
        except:
            self.interface.update_status(False)

    def format_message(self, message):
        """
        Appelle la méthode qui renvoit un message formatté
        """
        return format_message(self.MAGIC_NUMBER, self.VERSION_NUMBER, message)

    def connect(self, add_port):
        """
        Envoie un hello court pour initialiser une connection
        """
        if add_port in self.POT_NEIGHS:
            self.POT_NEIGHS.remove(add_port)
        add_port = (resolve_add_v6(add_port[0]), add_port[1])
        message = self.format_message(["Hello", self.MY_ID, None])
        self.send_message(message, add_port)

    def routine(self):
        """
        Envoie les hellos
        """
        while not self.running.wait(randint(0,20)):
            # Envoie les long hello pour garder des voisins symétriques
            if datetime.today() >= self.DELAY_LHELLOS + self.LAST_HELLO:
                for n in self.NEIGHS.keys():
                    message = self.format_message([
                        "Hello",
                        self.MY_ID,
                        self.NEIGHS[n]["id"]
                    ])
                    self.send_message(message, n)
                self.LAST_HELLO = datetime.today()
            # Envoie les annonces de voisins
            if datetime.today() >= self.DELAY_ANNOUNCE + self.LAST_ANNOUNCE:
                for dest in self.NEIGHS:
                    for other_n in self.NEIGHS:
                        if other_n != dest:
                            message = self.format_message([
                                "Neighbour",
                                other_n
                            ])
                            self.send_message(message, dest)
                self.LAST_ANNOUNCE = datetime.today()
            # Ajoute des nouveaux voisins si jamais il en manque
            if len(self.NEIGHS) < self.MIN_NEIGHS and datetime.today() >= self.DELAY_DISCOVERIES + self.LAST_DISCOVERY:
                # Choisi des n voisins au hasard dans les voisins potentiels
                chosen = sample(self.POT_NEIGHS, min(8-len(self.NEIGHS), len(self.POT_NEIGHS)))
                for peer in chosen:
                    self.connect(peer)
                self.LAST_DISCOVERY = datetime.today()

    def receive(self):
        """
        Reçoit les données et les parse
        """
        while not self.running.is_set():
            self.sock.settimeout(1.0)
            try:
                (data, address) = self.sock.recvfrom(1024)
                add_port = (address[0], address[1])
                parse_data(data, add_port, self)
            except:
                pass

        # Stopping thread
        neighbours = copy.deepcopy(self.NEIGHS)
        for voisin in neighbours:
            self.send_goaway(voisin, 1)

    def dispatch(self):
        """
        Envoie les Data et timeout le voisin au
        """
        while not self.running.wait(randint(1,2)):
            # Débug
            recent_data = copy.deepcopy(self.RECENT_DATA)
            # Pour chaque message
            for key in recent_data.keys():
                to_pop = []
                for destination in recent_data[key]["dests"]:
                    trys_left = recent_data[key]["dests"][destination]["trys_left"]
                    last_try =  recent_data[key]["dests"][destination]["last_try"]
                    if trys_left == 0:
                        to_pop.append(destination)
                        # Il faut envoyer le go away
                        self.send_goaway(destination, 2, "Pas d'Ack dans les temps")
                    else:
                        if last_try is None or datetime.today() > timedelta(seconds=pow(2, 6 - trys_left)) + last_try:
                            data = recent_data[key]["tlv"]
                            message = write_msg(self.MAGIC_NUMBER, self.VERSION_NUMBER, data)
                            was_sent = False
                            for neigh in self.NEIGHS.keys():
                                if neigh == destination:
                                    self.send_message(
                                        write_msg(self.MAGIC_NUMBER, self.VERSION_NUMBER, data),
                                        neigh
                                    )
                                    recent_data[key]["dests"][destination].update(
                                        {
                                            "trys_left": trys_left - 1,
                                            "last_try": datetime.today()
                                        }
                                    )
                                    was_sent = True
                            if was_sent is False:
                                to_pop.append(destination)
                for desti in to_pop:
                    recent_data[key]["dests"].pop(desti)
            self.RECENT_DATA = recent_data
