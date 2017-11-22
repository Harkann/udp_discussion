# udp_discussion
L3/M1 network course ENS Paris-Saclay, peer-to-peer communication in UDP

## Requirements
  * python (>= 3.5.4)

### Modules
  * dns
  * socket
  * logging
  * datetime
  * time
  * struct
  * random
  * ipaddress

## TODO
  * Graphical interface
  * Inondation
  * Receiving Ack
  * Support IPv4
  * Proper configuration file
  * Proper logging

## HOW-TO
  ```python3
  client = protocol.Client(port_number,[protocol],[interface])
  client.start()
  ```
  `protocol` by default is `socket.AF_INET6`
  `interface` by default is `"CLI"`
