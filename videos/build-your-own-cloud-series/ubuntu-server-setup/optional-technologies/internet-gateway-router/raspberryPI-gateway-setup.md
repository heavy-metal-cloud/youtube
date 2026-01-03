# (OPTIONAL) Setup a Raspberry PI as a Gateway Router
Your servers will require Internet access for software updates, etc.  This document explains how to
configure a Raspberry PI as an internet gateway.
>(NOTE: The RaspberryPi must have both a WIFI and ethernet
interface for this to work)

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Setup the Raspberry PI
### Create an Image
(IMPORTANT!!!!!! Do NOT use the `bookworm` release of Raspberry Pi OS. This  release doesn't
have iptables compiled into the kernel which causes a LOT of issues. Instead, use the 
`legacy` release called `Bullseye`)

[https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)

### Initial Configurations
Insert the SD card into the Raspberry PI then power up the device. After a few minutes you'll add the following initial configurations:
- Set Country
- Create User
  - Create a user. For example `hmuser`
  - Enter a password like `password`
- Select Wifi
  - Select and enter your WIFI info
- Choose Browser
  - I chose Chromium here

### Change the Hostname
Once the UI loads, go to: `Preferences -> Raspberry Pi Configuration`
Next, update the `Hostname`.

In my case, I'm using `pi-router` as the hostname.

## Setting up Networking Easy Mode
The easiest way to get started is to use the UI to setup your WIFI network and Static routes

### Setting up Wifi
Wifi should already be setup from the initial install. However, you can click the wifi symbol
in the upper right-hand corner of the UI and setup WIFI there.

### Setting up the Ethernet static Route
Assuming the UI is loaded, click the wifi symbol in the upper-right hand corner near the clock.

- Select `Wireless & Wired Network Settings`
- Click `Interface` -> `Eth0`   (NOTE: You may need an ethernet cable connected to a switch etc.)
- Uncheck `Automatically configure empty options`
- Set `IPv4 Address` to `192.168.3.1/24`

To validate the network configuration, run the following command from a terminal prompt:

```shell
sudo ifconfig -a
```

### Select DHCPCD as the Network configuration mode
The Raspberry PI OS has two different modes of network operation `dhcpcd` and `NetworkManager`.
We want to make sure we're forcing the former.

```shell
sudo raspi-config
```

Select the following settings:
- `Advanced Options` -> `Network Config` -> `dhcpcd`

Click `Ok` then restart the Raspberry PI

## Setup the Router
### Turn on IP pass-through
```
sudo vi /etc/sysctl.conf
```
Uncomment the following line:  
`net.ipv4.ip_forward = 1`  
Restart the pass-through using the folowing command:  
```
sudo sysctl -p /etc/sysctl.conf
```

### Setup NAT
```
sudo iptables -t nat -A POSTROUTING -j MASQUERADE
```
Save the changes  
```
sudo /sbin/iptables-save
sudo apt-get install iptables-persistent
```

Restart your Raspberry PI

At this point your Raspberry PI should now be acting as a router.  You can configure your other servers
to use this server's IP address as their default gateway.

## (OPTIONAL) Turn off the UI on startup
To save resources, you can disable the UI on startup by performing the following steps:

From a terminal prompt, type:

```shell
sudo raspi-config
```

Select `System Options` -> `Boot / Auto Login` -> `Console`

Click `Ok`

Now the Raspberry Pi will boot up from a terminal prompt. 

>(NOTE: If you ever need to get to the UI
again, you can type the following from a terminal prompt to start it up)

```shell
### Start the UI from a terminal prompt
startlxde-pi
```

