"""
Based off: https://gist.github.com/cslarsen/11339448
"""

from socket import *
import time, sys

ETH_P_ALL = 3

def macStrToBytes(macStr):
  import binascii
  macbytes = binascii.unhexlify(macStr.replace(':', ''))

  return macbytes

def getMacAddr():
  from uuid import getnode as get_mac
  mac = get_mac()
  addrStr = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

  return macStrToBytes(addrStr)

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
    sendeth(getMacAddr(),
            macStrToBytes(input("Enter the Destination Mac Address.")),   # Put DEST_ADDR passed in Stdin via pipe from listener container
            b"\x06\x00",              # Raw Ethernet 2 Frame Type
            b"HELLO from the SENDER"))