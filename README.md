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

### Automatic Repro

Use [./run.sh](/run.sh) to run an automatic repro. Your output will look like:

```bash
$ ./run.sh
Sending build context to Docker daemon  602.1kB
Step 1/4 : FROM python:3
 ---> 336d482502ab
Step 2/4 : RUN apt-get update && apt-get install -y nano
 ---> Using cache
 ---> 5cee00913b09
Step 3/4 : COPY ./ethListen.py /ethListen.py
 ---> Using cache
 ---> a2667cd58e69
Step 4/4 : CMD python -u /ethListen.py
 ---> Using cache
 ---> 9743c680cc72
Successfully built 9743c680cc72
Successfully tagged eth-listener:latest
Sending build context to Docker daemon  602.1kB
Step 1/4 : FROM python:3
 ---> 336d482502ab
Step 2/4 : RUN apt-get update && apt-get install -y nano
 ---> Using cache
 ---> 5cee00913b09
Step 3/4 : COPY ./ethSender.py /ethSender.py
 ---> Using cache
 ---> e528077d48da
Step 4/4 : CMD python -u /ethSender.py
 ---> Using cache
 ---> 46061f2a53ca
Successfully built 46061f2a53ca
Successfully tagged eth-sender:latest
eth-listener
eth-sender
8391d06550a63fb8423be86876cd906a79720f6d52c0d8885ce2e102b8015768
Sent 35-byte Ethernet packet on eth0
XX:XX:XX:XX:XX:XX
^ Mac Address ^
Listening for packets
Received: Len: 78 bytes time: 1519123406.9721925 message: `:
                                                            $[8
                                                               $
Received: Len: 90 bytes time: 1519123407.0323486 message: `$B:|{
Received: Len: 90 bytes time: 1519123407.2033708 message: `$B:|{
Received: Len: 35 bytes time: 1519123407.2230816 message: HELLO from the SENDER
^C
```

If you see the line
```

Received: Len: 35 bytes time: 1519123407.2230816 message: HELLO from the SENDER

```

Then the sender successfully sent a raw ethernet frame, despite icc being enabled.

### Manual Repro Steps

1. Build the Listener image: `docker build -t "eth-listener" -f listener-Dockerfile .`
The [listener](/ethListen.py) listens for raw ethernet frames and prints any received data.
It also finds and prints it's layer 2 address. We will need this value to send it data.

2. Build the Sender image: `docker build -t "eth-sender" -f sender-Dockerfile .`
The [sender](/ethSender.py) sends the string "HELLO from the SENDER" to the listener. 
We will look for this string amongst the listener output.

3. Create the ICC Disabled network: `docker network create -o com.docker.network.bridge.enable_icc=false noicc`
`noicc` is the name of the network.

4. Make sure you have two shells open, one for the listening container, and one for the sender.

5. Start your listening container: 
```bash
$ docker run -it --network noicc --name eth-listener eth-listener
XX:XX:XX:XX:XX:XX
^ Mac Address ^
Listening for packets
...
```

**Copy the mac address value for the next step.**

6. Run the sending container in your second terminal
```bash
$ docker run -it --network noicc --name eth-sender eth-sender
"Enter the Destination Mac Address."
```

7. Paste the mac address from the listening container in the sending container terminal.

8. Observe the Listening container output for `HELLO from the SENDER`
```
$ docker run -it --network noicc --name eth-listener eth-listener
XX:XX:XX:XX:XX:XX
^ Mac Address ^
Listening for packets
Received: Len: 78 bytes time: 1519123587.8931577 message: `:vgG\vg
Received: Len: 78 bytes time: 1519123587.9433937 message: `:]qB
Received: Len: 90 bytes time: 1519123588.222616 message: `$:
Received: Len: 35 bytes time: 1519123588.2736714 message: HELLO from the SENDER
Received: Len: 32 bytes time: 1519123588.9437985 message:
```

**Disabling ICC on the bridge network didn't block the raw socket communication as we would have expected**

These contain more explanation to break it down.

## Bug Resolution (Workarounds)

It can be worked around by placing containers on different network bridges. That means using `docker network create` for every container. By default you can only create 31 containers. [Set the subnet on each network manually to get around this limitation](https://loomchild.net/2016/09/04/docker-can-create-only-31-networks-on-a-single-machine/).