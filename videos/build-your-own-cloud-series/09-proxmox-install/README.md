# Proxmox Installation

>(REFERENCE: [https://www.proxmox.com/en/proxmox-virtual-environment/get-started](https://www.proxmox.com/en/proxmox-virtual-environment/get-started))

## Create the Proxmox boot media
### Install Etcher
You will need a free USB stick and something like `Etcher` to write the ISO image. Etcher can be downloaded
at this location: [https://etcher.balena.io/](https://etcher.balena.io/)

### Download the Proxmox Iso
Download the latest Proxmox ISO here: [https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso](https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso)

### Write the ISO image to your USB drive using Etcher
Using the etcher application write the iso image of Proxmox to your USB stick.

## Install Proxmox
### Boot up a mini PC with the Proxmox USB stick
You may have to change your BIOS settings to make USB booting a priority.  Insert the USB
stick and boot up the mini computer

### Select the UI type
- Select `Install PRoxmox VE (Terminal UI)`
- Click `I Agree` to the EULA
- Select your hard drive and click `Next`

### Locale settings
- **Country** - `United States`
- **Timezone** - `America/Detroit`
- **Keyboard Layout** - `U.S. English`

### Password and e-mail setup
- Enter the Root password
- Enter a valid e-mail address

### Network settings
- **Management Interface** - Select your Ethernet NIC
- **Hostname (FQDN)** - Enter the hostname for this server. I'm using `proxmox01.heavymetalcloud.lan`
- **IP address (CIDR)** - You can override the DHCP address here. I'm using `192.168.3.4/24`
- **Gateway Address** - This is the IP address of your gateway router (the default route). I'm using `192.168.3.1`
- **DNS Server Address** - This is the address of your DNS resolution server. I'm using `192.168.3.2` here, which is my OPNSense server that is running DNS.

### Setting validation
Verify all your settings and select `Install`

This will take a few minutes to complete.

## Post Install Setup
### Login to the Web UI
>(IMPORTANT!!! After rebooting wait about 15 minutes or so for the web browser to load up)

The Login screen on the Proxmox server console will show the URL for connecting to Proxmox.
In my case, the URL was: [https://192.168.3.4:8006/](https://192.168.3.4:8006/)

### Set up the "pve-no-subscription" updates
>(REFERENCE: [https://www.youtube.com/watch?v=xD9Xyt2mdSI](https://www.youtube.com/watch?v=xD9Xyt2mdSI))

From the main Web UI screen, select the following from the left-hand window pane:
>(NOTE: `prxmox01` in the menu selection below is the hostname, your machine name may vary. The default name
> would be `pve` instead.)

- `Datacenter` -> `proxmox01` 

Next from the main window (left-hand side menu) select the following:
- `Updates` -> `Repositories`
- Click the `Add` button
- **Repositories** - Select `No Subscription` from the dropdown
- Click the `Add` button

### Disable the "Enterprise" updates
From the same section in Proxmox:
- `Datacenter` -> `proxmox01`

Next from the main window (left-hand side menu) select the following:
- `Updates` -> `Repositories`

Select the two APT Repositories where the `Components` column is "enterprise" or "pve-enterprise"
and then click the `Disable`.

Next, Click the `Reload` button to load updates.

### Setup TLS for the GUI domain name
From the same section in Proxmox:
- `Datacenter` -> `proxmox01`

Next from the main window (left-hand side menu) select the following:
- `System` -> `Certificates`

Click the `Upload Custom Certificate` button.  Find your self-signed certifcate and key files and click `Upload`.

The UI will reboot and the changes may take a few minutes to take effect. Once this is done, you should be able to access
the GUI using the hostname with TLS. In my case this would be [https://proxmox01.heavymetalcloud.lan:8006](https://proxmox01.heavymetalcloud.lan:8006
)

### Repeat the installation process for all Physical servers
Now that the first server is set up, repeat this process for the other physical server that will be
included in the Proxmox cluster. (In my case, I had to install Proxmox on a total of three physical servers.)

>(NOTE: You may lose the TLS configurations from the previous step after joining a server to the cluster. To fix this
> issue, you can reapply the TLS certs once the servers have joined the cluster.)

### Setup a Proxmox cluster 
>(IMPORTANT!!! This is a one-time operation to be performed on your first Proxmox server)

From the same section in Proxmox:
- `Datacenter` 

Next from the main window (left-hand side menu) select the following:
- `Cluster`

Click the `Create Cluster` button. Give the Cluster a name and use the default network:
- **Cluster Name**: In my case, I will be using `proxmox-cluster`
- **Cluster Network**: I will use the default for my LAN, which is 192.168.3.4
- Click the `Create` button.

## Expand the Proxmox Cluster
Now that the first physical server has created a Proxmox cluster, we can have the other servers `join` the cluster.

### Gather the Join information
From the node that created the cluster, go to the following menu items:

From the left-hand menu in Proxmox:
- `Datacenter`

Next from the main window (left-hand side menu) select the following:
- `Cluster`

Click the `Join Information` button. Now click `Copy Information`.  You will need this in the next step.

### Join a new Proxmox node to the cluster
On the new node, go to these menus:

From the left-hand menu in Proxmox:
- `Datacenter`

Next from the main window (left-hand side menu) select the following:
- `Cluster`

Click the `Join Cluster` button and paste the 'Join Information' from the previous step. Next, Enter the following fields:

- **Information** - This should already be populated with the Join information from the Proxmox cluster.
- **Peer Address** - This should be the IP address of the Proxmox cluster node. In my case, this is `192.168.3.4`.
- **Password** - You should enter the root password from the Proxmox cluster node here.
- **Fingerprint** - You can leave this default.
- **Cluster Network** - This should be the IP address of the node you want to join. In my case this is `192.168.3.6`
- **peer's link address** - This field can't be modified and should contain the IP address of the Proxmox Cluster Node. (192.168.3.4 for me)
- Click the `Join Proxmox-cluster` Button

The join process will take a few minutes.

>(NOTE: If you added TLS certificates to this Join node, you may have to add them again once the node has joined the cluster.)


## Troubleshooting
### Cleanup old Ceph paritions
First, let's examine the partitions
```shell
lsblk -f

## or
lsblk -l
```

```
### Example output below
NAME                  FSTYPE      LABEL UUID                                   MOUNTPOINT
vda
└─vda1                LVM2_member       eSO50t-GkUV-YKTH-WsGq-hNJY-eKNf-3i07IB
  ├─ubuntu--vg-root   ext4              c2366f76-6e21-4f10-a8f3-6776212e2fe4   /
  └─ubuntu--vg-swap_1 swap              9492a3dc-ad75-47cd-9596-678e8cf17ff9   [SWAP]
vdb
```

Find the Ceph partition
```shell 
### Check to see if the Ceph Filesystem is still mapped:
sudo dmsetup ls --tree

#### If you see something like this, it's still mapped:
ceph--a00eb6ee--28d7--4251--b206--6825c5ef8628-osd--data--021841c9--ca80--4ff5--ae24--65b6c50b11ee (253:0)
 └─ (8:0)
 
 
#### Remove the mapping:  (using the example above)
sudo dmsetup remove ceph--a00eb6ee--28d7--4251--b206--6825c5ef8628-osd--data--021841c9--ca80--4ff5--ae24--65b6c50b11ee

#### Now check the mapping again:
sudo dmsetup ls --tree

### it should look like this:
No devices found

#### Running this command should show an empty 'sda' drive now (NOTE: Your drive may be different
#### than 'sda'
lsblk -f
```

### Can't remove proxmox from a hard drive (You can't install another OS)
Sometimes with Ubuntu, you'll get strange errors when trying to install it over an existing Proxmox install. 

What I found that works, is the following:

- Reinstall Proxmox (fresh install)
- Then install Ubuntu after. 

If you still have issues, you may have to try deleting the partitions that were created for Proxmox