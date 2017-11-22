from tkinter import Text, Tk, Button, Label, Event, Toplevel, messagebox
from tkinter.scrolledtext import ScrolledText
from random import randint
import struct
import time
import copy

class Interface():

    def __init__(self,client):
        self.root = Tk()
        self.client = client
        self.is_log = False
        self.is_neighs = False

        self.RECENT_DISPLAY = []

        self.txt = ScrolledText(self.root, borderwidth=3, relief="sunken")
        self.txt.config(font=("consolas", 12), undo=True, wrap='word')
        self.txt.config(state="disabled")
        self.txt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2, columnspan=3)
        self.txt.tag_configure("warning", background="orange")
        self.txt.tag_configure("error", background="red")

        self.input_txt = Text(self.root, borderwidth=3, relief="sunken")
        self.input_txt.config(font=("consolas", 12), undo=True, wrap='word', height=1)
        self.input_txt.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        self.input_txt.bind("<Return>", self.event_handler)
        self.input_txt.focus_set()

        self.send_button = Button(self.root, text="Send", command=self.send_text)
        self.send_button.grid(row=1, column=2)

        self.nick = Label(self.root)
        self.nick.grid(row=1, column=0)
        self.update_nick()

        self.neighbours = Label(self.root)
        self.neighbours.grid(row=2, column=0)
        self.update_neighs()

        self.status = Label(self.root)
        self.status.grid(row=2, column=2)
        self.update_status(False)

        self.butt_log = Button(self.root, text="Logs", command=self.show_logs)
        self.butt_log.grid(row=1, column=3)
        self.butt_close = Button(self.root, text="Close", command=self.close_client)
        self.butt_close.grid(row=2, column=3)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.close_client()

    def close_client(self):
        self.insert_warn( "Shutting down client")
        self.client.kill_all()
        self.root.destroy()

    def show_logs(self):
        self.is_log = True
        self.log_win = Toplevel(self.root)
        self.log_txt = ScrolledText(self.log_win)
        self.log_txt.grid(row=0, column=0)
        self.log_txt.tag_configure("warning", background="orange")
        self.log_txt.tag_configure("error", background="red")
        self.log_txt.tag_configure("send", background="green")
        self.log_txt.tag_configure("received", background="blue")

        def close_logs():
            self.is_log = False
            self.log_win.destroy()


        self.butt_close_logs = Button(self.log_win, text="Close", command=close_logs)
        self.butt_close_logs.grid(row=1, column=0)

    def add_log(self, log, tag=None):
        if self.is_log:
            self.log_txt.config(state="normal")
            self.log_txt.insert("end", log.strip()+"\n", tag)
            self.log_txt.config(state="disabled")

    def update_status(self, online):
        if online:
            self.status.config(background="green",text="ONLINE ")
        else:
            self.status.config(background="red",text="OFFLINE")

    def update_nick(self):
        self.nick.config(text=self.client.NICK)

    def update_neighs(self):
        self.neighbours.config(text="Neighs : {}, Sym : {}, Pot : {}".format(
            len(self.client.NEIGHS.keys()),
            len(self.client.NEIGHS.keys()),
            len(self.client.POT_NEIGHS)
        ))

    def event_handler(self, event):
        if event.keysym =="Return":
            self.send_text()

    def insert_text(self,text, tag=None):
        self.txt.config(state="normal")
        self.txt.insert("end", text.strip()+"\n", tag)
        self.txt.config(state="disabled")

    def send_text(self):
        message = self.input_txt.get(1.0,"end").strip()
        self.input_txt.delete(1.0,"end")
        if message == "":
            pass
        elif message[0] == "/":
            commande = message.split(" ")
            self.apply_commande(commande)
        else:
            nonce = randint(0, 2**32-1)
            self.client.add_to_recent( self.client.MY_ID, nonce, "{}: {}".format(self.client.NICK, message))

    def insert_warn(self, message):
        warn = "[WARNING]: {}".format(message)
        self.insert_text(warn, "warning")

    def apply_commande(self, commande):
        if commande[0] == "/nick":
            self.client.NICK = commande[1]
            self.update_nick()

        elif commande[0] == "/me":
            action = " ".join(commande[1::])
            nonce = randint(0, 2**32-1)
            self.client.add_to_recent( self.client.MY_ID, nonce, "* {} {}".format(self.client.NICK, action))

        elif commande[0] == "/connect":
            if len(commande) != 3:
                 self.insert_warn( "'{}' need 2 arguments".format(commande[0]))
            else:
                addresse = commande[1]
                port = commande[2]
                self.client.connect((addresse, int(port)))

        elif commande[0] == "/disconnect":
            if len(commande) == 2 and commande[1] == "all":
                for voisin in copy.deepcopy(self.client.NEIGHS):
                    self.client.send_goaway(voisin, 1)
            elif len(commande) == 3:
                self.client.send_goaway((commande[1], commande[2]), 1)
            else:
                self.insert_warn( "'{}' need 3 arguments".format(commande[0]))

        elif commande[0] == "/close":
            self.close_client()

        elif commande[0] == "/help":
            self.insert_warn( "HELP")
            self.insert_text(" * /help")
            self.insert_text(" * /nick Nickname")
            self.insert_text(" * /me Action")
            self.insert_text(" * /connect [address port]")
            self.insert_text(" * /disconnect [all] [address port]")
            self.insert_text(" * /close")

        else:
            self.insert_warn( "Unknown  command '{}'".format(commande[0]))
