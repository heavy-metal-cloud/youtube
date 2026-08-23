# Install Ceph into a Proxmox cluster
Installing Ceph will give you distributed storage with High Availability from a single node failure. One
of the main benefits is you can share VM templates across nodes more easily.

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## Dependencies
### A 3 node Proxmox cluster that is running
At this point, you should already have Proxmox installed and have
at least 3 nodes joined in a cluster.

### A free hard drive on each node, dedicated for Ceph
You should have a free hard drive that is wiped clean and ready for Ceph on each of your nodes (minimum of three)

## Install Ceph
### Ceph installation (per node)
>(NOTE: You will have to perform these steps with each node)

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>` - `Ceph`

Click the `Install Ceph` button and select the following options:

**Info** Tab
- **Ceph version to install** - You should use the latest version here. I'm using `tentacle (20.2)`
- **Repository** - Select `No-Subscription`
- Click the `Start tentacle installation` button

**Installation** tab
Press enter or click `Y` to start the installation. Click `Next` when the installation is has completed successfully.

**Configuration** tab
- **Public Network IP/CIDR** - Select the default value here. This should be the same as your Ethernet port LAN network.
- **Cluster Network IP/CIDR** - Select `Same as Public Network` 
- Click `Next`

**Success** tab
You should see `Installation successful!` here along with some next steps.

### Create an OSD (per node)
From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>` 

Next from the main window (left-hand side menu) select the following:
- `Ceph` -> `OSD`

Click `Create: OSD`
- **Disk** - Select a free available disk. In my case, I'm using a small SSD
- Click the `Create` button.

>(IMPORTANT!!! If you don't see any available disks in the dropdown, this means either you don't have a free disk
> available for ceph, or this disk isn't completely wiped clean. (no partitions or filesystem)
> 
> The `Cleanup old Ceph partitions` in the troubleshooting sections describes the process for cleaning up the drive in this case.)

### Create Ceph Monitors and Managers (per node)
From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>`

Next from the main window (left-hand side menu) select the following:
- `Ceph` -> `Monitor`

In the top **Monitor** section Click `Create`
- **Host** - Select a free Host to add the monitor
- Click the `Create` button.

On the top **Manager** section Click `Create`

- **Host** - Select a free Host to add the manager
- Click the `Create` button.

>(NOTE: The goal here is to have one monitor and manager installed per node, for redundancy)

### Create a Pool (once per cluster)
A pool is like a shared drive across all your Proxmox nodes for VM disks

>(NOTE: You only have to perform this operation on one node. The changes will span all nodes in the cluster)

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>` 

Next from the main window (left-hand side menu) select the following:
- `Ceph` -> `Pools`

Click `Create`
- **Name** - You can call your pool anything. I'm using `ceph-pool-01`
- **Size** - Select `3` here, for three replicas of the data
- **PG Autoscaler Mode** - Select `on`
- **Add as Storage** - This should be checked
- Click the `Create` button.

You should now see a new disk listed under each Proxmox node called `ceph-pool-01`

### Create a CephFS mount
A CephFS mount will allow us to share ISO images, snippets, etc. across nodes.

>(NOTE: You can't store ISO images and snippets in a pool. That's where this CephFS comes into play)

>(NOTE2: You only have to perform this operation on one node. The changes will span all nodes in the cluster, similar to a pool)

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>`

Next from the main window (left-hand side menu) select the following:
- `Ceph` -> `CephFS`

Click `Create` under the 'Metadata Servers' section
- **Host** - This will be the node name. For example: `proxmox01`
- **MDS ID** - Again, this will be the node name. For example: `proxmox01`
- Click the `Create` button.

>(NOTE: Repeat this process for the other Proxmox nodes you have. In my case I created metadata servers for
> proxmox02 and proxmox03)

Now the `Create CephFS` button should be blue at the top of the window pane.  Click it and use the default values.

At this point you should see a disk called `cephfs` appear in all your Proxmox nodes.

### Enable ISO, Snippets, etc on the 'cephfs' storage
To use custom cloud init scripts, you will need to enable `snippets`. This will provide an area where files can be shared
with the VM's

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>` - `Shell`

In the shell, run the following command:
```shell
pvesm set cephfs --content images,rootdir,vztmpl,backup,iso,snippets
```

## VM Setup across all nodes

### Install Operating System (OS) images
From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>` -> `cephfs`

Now, in the center window pane, you will have another left-hand menu. Select the following:

- `ISO Images` -> `Download from URL`

In the popup window use the following settings:
- **URL**: https://cloud-images.ubuntu.com/minimal/releases/oracular/release/ubuntu-24.10-minimal-cloudimg-amd64.img
- Click the `Query URL` button
- Click the `Download` button

### Add a custom cloud-init 'User' file
Before we get started, for my VM's I want to add public SSH keys for login and self-signed certificate authorities. Also, I will be using
this file to initially install k3s, etc.  To do this, we will use a cloud-init configuration file.

From this directory, take a look at the [cloud-init_files/cloud-init-user.yaml](cloud-init_files/cloud-init-user.yaml) file. Modify
the SSH public key and Certificate Authority information, as needed.

>(NOTE: If you're using a self-signed certificate authority (CA), make sure to also include any subordinate (intermediate) certs in the chain, as well.)

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `<NODE_NAME>` - `Shell`

From the shell perform the following steps:

>(IMPORTANT!!! If the `snippets` directory is missing, you will have to run the command in the `Enable Snippets on the 'local' storage` section above!!!)

```shell
cd /mnt/pve/cephfs/snippets

### (NOTE: You can use any editor here. I'm using VI to create the cloud-init user config file.)
## Paste the contents of your cloud-init-user.yaml file and then save/close the file.
vi cloud-config-user.yaml
```

### Create a VM Template (for cloud-init images) using CephFS
To create a VM for cloud-init images, we'll use the CLI instead of the UI interface. Cloud init images
require a virtual hard drive to hold the OS and a virtual CD-ROM drive to hold the cloud init data which will be
used to boot and install the OS.

>(REFERENCES:
> - [https://pve.proxmox.com/pve-docs/qm.1.html](https://pve.proxmox.com/pve-docs/qm.1.html)
> - [https://www.youtube.com/watch?v=Kv6-_--y5CM](https://www.youtube.com/watch?v=Kv6-_--y5CM)
    > )

From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter` -> `proxmox01` - `Shell`

```shell
### Create a VM with:
## - Identifier (ID): This should be a number greater than 1000 since Proxmox uses 100 to start by default. I'm using 5000 here.
## - name: "ubuntu-cloud" (This can be anything you want)
## - core: 2 cores
## - cpu: cputype `host` will use the underlying CPU instructions instead of a virtual instruction set.
## - memory: 4GB of virtual memory
## - balloon: zero is to prevent the VM from expanding memory dynamically, which can cause problems.
## - ciuser: The default user of the VM. I'm using 'ubuntu'
## - ipconfig0: We want to default the IP address of the VM to use DHCP
## - cicustom: This allows us to use a custom Cloud-init script during start. (NOTE: we created this in the previous section)
## - agent: This enables the QEMU agent on the VM. 
## - net0: This uses virtio as the networking subsystem. The bridge used is the default network shared by your NIC
## - serial0: This creates a virtual serial port
## - vga: This is like virtually plugging in a VGA monitor into the serial port we just created
## - ide2: This creates a virtual CD-ROM drive that stores the cloud-init information. I'm using `ceph-pool-01:cloudinit`. The CD-ROM "disc" will be called: 'vm-5000-cloudinit'
#### (NOTE: for ide2, you could also use `local-lvm:cloudinit:cloudinit` to store the VM locally instead of the shared ceph pool.
qm create 5001  --name ubuntu-cloud \
  --core 2 --cpu cputype=host \
  --memory 4096 --balloon 0 \
  --ciuser ubuntu --ipconfig0 ip=dhcp \
  --cicustom "user=cephfs:snippets/cloud-config-user.yaml" \
  --agent enabled=1 \
  --net0 virtio,bridge=vmbr0 \
  --serial0 socket --vga serial0 \
  --ide2 ceph-pool-01:cloudinit 

### Navigate to the location where you downloaded the Ubuntu OS images
cd /mnt/pve/cephfs/template/iso
ls 

### Create a Virtual disk with the contents of the OS image and import it into VM 5001
## (NOTE: 'local-lvm' is the default disk created by Proxmox. If you have other drives, you can use those instead.
##
## This will create a virtual disk called 'vm-5001-disk-0', which is named after the ID of the VM (5001)
##
## (IMPORTANT!!! This step is a little confusing. You're setting up a drive for VM 5001 with the ISO contents, but it
## hasn't been "plugged in" to the VM yet. The next step will handle that.)
qm importdisk 5001 ubuntu-24.10-minimal-cloudimg-amd64.img ceph-pool-01

### In this step we're treating the virtual disk we created in the previous step like a new SCSI drive and attaching it to the VM
## (It's like plugging in a hard drive into your motherboard. You're attaching it to the VM at SCSI port 0)
##
## "ssd=1" will treat the drive as an ssd to allow for reclaimed storage space.
qm set 5001 --scsihw virtio-scsi-pci --scsi0 ceph-pool-01:vm-5001-disk-0,ssd=1

### The default size for a disk is 3.5G. Let's expand the size to 20G
## (NOTE: The name of the disk created in the previous step is 'scsi0")
qm disk resize 5001 scsi0 20G

### Set the boot options to use the 'scsi-0' drive to boot the VM
qm set 5001 --boot c --bootdisk scsi0
```

### Create a Template from the VM
Run the following command to create a template from the VM we just configured. This will allow us to quickly spin up
similar VM's

```shell
qm template 5001
```

### Clone a VM from the Template
Run the following command to create a VM from the template we just defined.

```shell
### (NOTE: 5000 is the template ID, 100 is the first available id for the VM clone
### specifying `--full` makes a full clone that copies the disk and doesn't try to reference the template.)
qm clone 5001 100 --name my-vm --full true
```

### (OPTIONAL) Use a Static IP address / Name server
>(REFERENCE: [https://pve.proxmox.com/pve-docs/qm.1.html](https://pve.proxmox.com/pve-docs/qm.1.html))

```shell
### Set a static IP address and default gateway
qm set 100 --ipconfig0 ip=192.168.3.240/24,gw=192.168.3.1

### Set the DNS server
qm set 100 --nameserver 192.168.3.2
```

### (OPTIONAL) Resize the hard drive
```shell
qm disk resize 100 scsi0 30G
```

### Start the VM
```shell
### This assumes the VM id is 100
qm start 100
```

### Find the IP address of the VM
```shell
### This assumes the VM id is 100
qm agent 100 network-get-interfaces | grep ip-address
```

### SSH Into the VM
You should now be able to SSH into the VM using `ubuntu` as the user and also your SSH private key that is
associated with the public key that you included in the `cloud-init-user.yaml` file.

## Set up High Availability (HA) for the VMs
Now that you have a cluster with shared storage, it's possible to define VM's as Highly Available (HA). With this
setting in place, a VM will automatically be moved to an active node, if the node it's running on goes offline, for whatever
reason.

### Setting HA for a VM using the GUI
From the main Web UI screen, select the following from the left-hand window pane:
- `Datacenter`

Now, in the center window pane, you will have another left-hand menu. Select the following:

- `HA` 
- Click the `Add` button

Select the VM that you want to make Highly Available (HA). In my case, I will select VM `100`.
- Click the `Add` button

You should now see the VM added to the list of resources that are managed by HA. If the node running VM 100 goes down
it should be migrated and started on a running node. (NOTE: This might take a few minutes)

>(NOTE: Sometimes the VM will move but won't be able to start on its own. In this case, just manually start the migrated VM)

### Setting HA for a VM using the CLI
>(REFERENCE: [https://pve.proxmox.com/wiki/High_Availability](https://pve.proxmox.com/wiki/High_Availability))

From a shell run the following command:

```shell
ha-manager add vm:100
```

To change the state of the VM, you can also run this command.
```shell
### NOTE, this is OPTIONAL!!!
ha-manager set vm:100 --state stopped

# or
ha-manager set vm:100 --state started
```

To remove the VM from the HA Manager, you can run the following command:
```shell
ha-manager remove vm:100
```

## Troubleshooting
### Troubleshooting commands:
```shell
systemctl status ceph-osd@*

ceph osd tree up
ceph osd tree down
ceph osd tree out

##### Restart an OSD #####
## systemctl restart ceph-osd@<CEPH_NODE_ID>
# For example
systemctl restart ceph-osd@0
```

### An OSD is down
If one (or more) of the OSD's is down, try restarting the OSD service on the Proxmox node running ceph:

```shell
## systemctl restart ceph-osd@<CEPH_NODE_ID>
# For example
systemctl restart ceph-osd@0
```

### Cleanup old Ceph partitions
>(IMPORTANT!!!! Careful here! Running these commands will erase your hard drive! Any data you have will be lost!)

If you're having issues creating an OSD, it could be caused by one of two issues:

1) A dedicated empty drive isn't installed for ceph
2) A dedicated drive is installed, but isn't completely empty

The following instructions will solve the second issue.

First, let's examine the partitions
```shell
lsblk -f
```

```
### Example output below
NAME                                                                                                  MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
sda                                                                                                     8:0    0 223.6G  0 disk
└─ceph--2e28fe22--620f--4bbb--971d--2d3e259bb662-osd--block--72dcdf1a--f525--4468--8f24--beef8d315faf 252:0    0 223.6G  0 lvm
nvme0n1                                                                                               259:0    0 931.5G  0 disk
├─nvme0n1p1                                                                                           259:1    0  1007K  0 part
├─nvme0n1p2                                                                                           259:2    0     1G  0 part /boot/efi
└─nvme0n1p3                                                                                           259:3    0 930.5G  0 part
  ├─pve-swap                                                                                          252:1    0     8G  0 lvm  [SWAP]
  ├─pve-root                                                                                          252:2    0    96G  0 lvm  /
  ├─pve-data_tmeta                                                                                    252:3    0   8.1G  0 lvm
  │ └─pve-data                                                                                        252:5    0 794.3G  0 lvm
  └─pve-data_tdata                                                                                    252:4    0 794.3G  0 lvm
    └─pve-data              

```

Find the Ceph partition
```shell 
#### If you see something like this, it's still mapped:
ceph--2e28fe22--620f--4bbb--971d--2d3e259bb662-osd--block--72dcdf1a--f525--4468--8f24--beef8d315faf
 └─ (8:0)
 
 
#### Remove the mapping:  (using the example above)
sudo dmsetup remove ceph--2e28fe22--620f--4bbb--971d--2d3e259bb662-osd--block--72dcdf1a--f525--4468--8f24--beef8d315faf


#### Running this command should show an empty 'sda' drive now (NOTE: Your drive may be different
#### than 'sda'
lsblk -f
```

(Optional) Remove a partition
```shell
### First, let's see if there's a partition on the drive
lsblk -f
```

```
NAME               FSTYPE      FSVER    LABEL UUID                                   FSAVAIL FSUSE% MOUNTPOINTS
sda                LVM2_member LVM2 001       2yS09l-rZ9z-9TUz-cFzR-r8Ac-RgfB-BAqbfC
nvme0n1
├─nvme0n1p1
├─nvme0n1p2        vfat        FAT32          85EE-C5C6                              1010.3M     1% /boot/efi
└─nvme0n1p3        LVM2_member LVM2 001       ijvh8q-QV07-JAGx-JfEC-iyMr-EsVL-pBJcdz
├─pve-swap       swap        1              da4f5e28-4289-4933-8d7f-26cba6b0b140                  [SWAP]
├─pve-root       ext4        1.0            ef8152c2-fe65-43d8-9c44-6004de3decdc       86G     3% /
├─pve-data_tmeta
│ └─pve-data
└─pve-data_tdata
└─pve-data
```

If you see something like this:
```
sda                LVM2_member LVM2 001       2yS09l-rZ9z-9TUz-cFzR-r8Ac-RgfB-BAqbfC
```

Then the drive has a partition that needs to be cleaned out. Run the following command:
```shell
sudo wipefs -a /dev/sda

### Then verify that the partition is gone
lsblk -f
```

At this point, you should be able to create an OSD in ceph