import socket
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

pot_neighbours = []  # format : (ip,port)
neighbours = {}  # format : (ip,port) : [id,date_last_h,date_last_long_h]

print(message)
