"""
Based off: https://gist.github.com/cslarsen/11339448
"""

from socket import *
import time

ETH_P_ALL = 3

def printMacAddr():
  from uuid import getnode as get_mac
  mac = get_mac()
  addrStr = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

  # addrStr piped to ethSender, important it's printed first
  print(addrStr)
  print("^ Mac Address ^")

def printPacket(packet, now, message):
  packetMessage = packet[14:].decode('ascii', 'ignore')

  if packetMessage == "hello":
    print ("Got message from sender.")

  print(message, "Len:", len(packet), "bytes time:", now, "message:", packetMessage)

def listeneth(interface = "eth0"):
  s = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL))

  # From the docs: "For raw packet
  # sockets the address is a tuple (ifname, proto [,pkttype [,hatype]])"
  s.bind((interface, 0))
  s.setblocking(0)

  while True:
    now = time.time()

    try:
      packet = s.recv(128)
    except Exception as e:
      if 'Resource temporarily unavailable' not in str(e):
        print(e)
      pass
    else:
      printPacket(packet, now, "Received:")

    time.sleep(0.001001)

if __name__ == "__main__":
  # MacAddr piped to ethSender, important it's printed first
  printMacAddr()

  print("Listening for packets")
  listeneth()