# Tiny Pilot - Remote Keyboard Video Mouse (KVM) server
Tiny Pilot is a KVM service that allows you to connect HDMI and USB ports to a server and control it remotely,
using web browser.

I will be using this to show the installation process of Operating systems for my YouTube videos.

>(REFERENCES:
> - [https://tinypilotkvm.com/](https://tinypilotkvm.com/)
> - [https://github.com/tiny-pilot/tinypilot](https://github.com/tiny-pilot/tinypilot)
> - [https://mtlynch.io/tinypilot/#how-to-build-your-own-tinypilot](https://mtlynch.io/tinypilot/#how-to-build-your-own-tinypilot)
    >)

## Hardware Dependencies
To build out the Tiny Pilot you will need a few things. These are listed in the links in the reference section above, but
I will also cover the hardware I'm using:

>(IMPORTANT!!!!! The Raspberry PI absolutely MUST be the 4B variant. Newer or older versions WILL NOT work!)

- Raspberry Pi 4B
- SD card with Raspberry Pi OS Lite installed (see below)
- AC Power adapter using a USB-C connector. (27 Watt, Raspberry PI branded adapter)
- Tiny Pilot Power Connector (https://tinypilotkvm.com/products/tinypilot-power-connector)
- HDMI and USB cables required to connect everything up.

## Flash Raspberry Pi OS Lite using Etcher
### Install Etcher
You will need a free USB stick and something like `Etcher` to write the ISO image. Etcher can be downloaded
at this location: [https://etcher.balena.io/](https://etcher.balena.io/)

### Download the Raspberry Pi OS Lite ISO
>(IMPORTANT!!!! You MUST use the 32 bit version of Raspberry Pi OS 11, called Bullseye)

Download the 32 bit version of Raspberry Pi OS (Bullseye) ISO here:
- [https://downloads.raspberrypi.org/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2024-07-04/](https://downloads.raspberrypi.org/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2024-07-04/)

### Write the ISO image to your Micro SD card using Etcher
Using the etcher application write the ISO image of Raspberry Pi OS Lite to your Micro SD card.

## Initial Boot Up and settings
Install a Keyboard and monitor to the Raspberry pi, then boot it up by plugging in the power cable.

### Set the keyboard type and create a user
I set my keyboard to:

- English (US)

My username is `hmuser`

### Run raspi-config to set things up
From a command prompt, run the following:

```shell
sudo raspi-config
```

Select the following options:

**3 Interface Options**
- **I1 SSH** - Select `Yes` to enable the SSH server

**Advanced Options**
- **AA** Network Config
    - **2** NetworkManager - This should be set to active

### Setup the Ethernet port with a Static IP address
Run the following command:

```shell
### Find the ethernet NAME or DEVICE. For example, the for mine is "Wired connection 1"
nmcli con show

### Next run the following command to set the IP address, etc.
nmcli con modify <connection_name> ipv4.method manual ipv4.addresses <static_ip_address>/<netmask_bit_count> ipv4.gateway <gateway_ip_address> ipv4.dns "<primary_dns_server>,<secondary_dns_server>"

# For example:
sudo nmcli con modify "Wired connection 1" \
  ipv4.method manual \
  ipv4.addresses 192.168.3.9/24 \
  ipv4.gateway 192.168.3.1 \
  ipv4.dns "192.168.1.254,8.8.8.8"
```

Now check that the IP has been applied to the interface and test
```shell
### View network interfaces
ip a

### Ping google to test DNS and IP connectivity
ping www.google.com
```

## Install Tiny Pilot
### Install the Tiny Pilot software

```shell
curl -sS https://raw.githubusercontent.com/tiny-pilot/tinypilot/master/quick-install \
  | bash -
sudo reboot
```
