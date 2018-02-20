# Docker Layer 2 ICC Bug

## Explanation (What and How)

When you create a docker container using `docker run`, it is automatically connected to a bridge network. Unless inter-container communication (ICC) was disabled in the docker daemon, every container on that bridge network can communicate with one another via sockets.

Docker allows you to restrict ICC in two ways:
1. Restricting it in the kernel with `"icc": false` in `daemon.json`
2. Creating a network like `docker network create -o com.docker.network.bridge.enable_icc=false noicc` then connecting containers to it with `docker run --network=noicc ...`

In both cases you expect that all network communications will be blocked between the containers themselves. As demonstrated below, this is not the case. Docker puts in iptables rules that block communications on layer 3, but layer 2 communications are allowed. What this means, is I can still send data between the containers over a socket.

**Disabling ICC doesn't block raw ethernet frames between containers.**

This behavior is highly unexpected, and in highly secure environments, likely to be an issue.

## Repro Steps
I reproed this using `Docker-CE for Mac Version 17.09.0-ce-rc3-mac30 (19329)`.

These repro steps are a little complicated because I didn't want to parse the output of `ip a` and I don't know a way to get the layer 2 address from outside the containers. 

1. Get the python image, it is a large one: `docker pull python:latest`
2. Create the ICC Disabled network: `docker network create -o com.docker.network.bridge.enable_icc=false noicc`
3. Make sure you have two shells open, one for the listening container, and one for the sender.
4. Start your listening container: `docker run -it --network noicc --name ethListen --rm python bash`
5. Get the layer 2 address, inside Listening Container, I'll refer to this as (DEST_ADDR): `ip a`
Your output will look like this, you are looking for the highlighted value.

![Ip A output](/ip_a.png)

6. Copy the contents of `ethListen.py` (from this repo) into the listening container. I installed and used nano.
```
$ apt-get update 
$ apt-get install -y nano
$ nano ethListen.py
```

7. Run `ethListen.py` in the listening container to listen for raw ethernet frames.
```
$ python ethListen.py
Listening for packets

```

8. Now we need to set up the sending container: `docker run -it --network noicc --name ethSend --rm python bash`

9. Get the layer 2 address, inside sending container, as we did above for the listening container. I'll refer to this as (SRC_ADDR).

10. Edit the contents of ethSend.py (in this repo). Replacing the DEST_ADDR and SRC_ADDR to the ones from your containers. Example values that were in my containers are already in ethSend.py to show how they should be formatted. For example `02:42:ac:18:00:02` becomes `b"\x02\x42\xAC\x11\x00\x02"`.

11. Copy the contents of `ethSend.py` (from this repo) into the sending container. I installed and used nano.
```
$ apt-get update 
$ apt-get install -y nano
$ nano ethSend.py
```

12. Run `ethSend.py` in the sending container to send one raw packet. Run it as many times as you like to send more packets.
```
$ python ethSend.py
Sent 19-byte Ethernet packet on eth0
```

13. Now examine the output on the listening container (there may be more frames than just this one, but look for the matching byte count):
```
Listening for packets
Received: 19 bytes time: 1519095710.6201906
```

**Disabling ICC on the bridge network didn't block the raw socket communication as we would have expected**

## Bug Resolution (Workarounds)

It can be worked around by placing containers on different network bridges. That means using `docker network create` for every container. By default you can only create 31 containers. [Set the subnet on each network manually to get around this limitation](https://loomchild.net/2016/09/04/docker-can-create-only-31-networks-on-a-single-machine/).