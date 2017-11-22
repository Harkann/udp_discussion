MAGIC_NUMBER = 93
VERSION_NUMBER = 0
PORT = 1337
ALLOWED_TYPES = {
    0: "Pad1",
    1: "PadN",
    2: "Hello",
    3: "Neighbour",
    4: "Data",
    5: "Ack",
    6: "GoAway",
    7: "Warning",
}
DELAY_LHELLOS = 20 # seconds
DELAY_DISCOVERIES = 60 # seconds
DELAY_ANNOUNCE = 60 # seconds
NICK = "Mikachu"
DEFAULT_POT = [
    ("jch.irif.fr", 1212),
    ("2a06:e042:0100:0004:ebd9:fe06:9e3f:0112", 7331),
    ("2a06:e042:0100:0c04:e0e9:d6d3:4012:5924", 7331)
]
