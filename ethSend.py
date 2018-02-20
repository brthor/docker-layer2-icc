"""
Based off: https://gist.github.com/cslarsen/11339448
"""

from socket import *
import time

ETH_P_ALL = 3

def sendeth(src, dst, eth_type, payload, interface = "eth0"):
  """Send raw Ethernet packet on interface."""

  assert(len(src) == len(dst) == 6) # 48-bit ethernet addresses
  assert(len(eth_type) == 2) # 16-bit ethernet type

  s = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL))

  # From the docs: "For raw packet
  # sockets the address is a tuple (ifname, proto [,pkttype [,hatype]])"
  s.bind((interface, 0))
  s.setblocking(0)

  ret = s.send(dst + src + eth_type + payload)

  return ret

if __name__ == "__main__":
  print("Sent %d-byte Ethernet packet on eth0" %
    sendeth(b"\x02\x42\xAC\x11\x00\x03",   # Put SRC_ADDR Source Address (run `ip a` in sending container)
            b"\x02\x42\xAC\x11\x00\x02",   # Put DEST_ADDR Destination Address (run `ip a` in listening container)
            b"\x06\x00",                   # Raw Ethernet 2 Frame Type
            b"hello"))