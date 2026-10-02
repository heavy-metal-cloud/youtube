# Setting up the Zima Board 2
This document walks through the steps of setting up the Zima Board 2. For my specific Use Case, I will be
using the Zima Board as a NAS server. The NAS server will mount to DGX Spark servers for serving large models.

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)
- 
>(REFERENCE: [https://shop.zimaspace.com/products/zimaboard2-single-board-server](https://shop.zimaspace.com/products/zimaboard2-single-board-server))

## Hard drive setup
>(NOTE: I'm assuming you will be installing at least 1 SSD hard drive)

Using the SSD connection cable, connect both SATA connectors and the power adapter to the back of the Zima Board 2. Connect the
other end(s) to one or two hard drives.

## Initial Set Up
>(NOTE: For this initial set up, I'll assume you have a DHCP server running on the ethernet network. In my case, I'm using
> an OPNSense server to provide this functionality.)

Connect the Zima board to a monitor, keyboard, and ethernet cable. Power up the Zima board to continue..

### Setting a Root password
From the initial startup screen, press `ALT - F12`. This will drop you into a shell login. The user is `root`.  Next
run the following command to set the password:


```shell
passwd
## Enter your password twice.
```

## Setting up the Zima board using the Web portal.
### Locate the address and bring up the portal
To find the IP address of the device from the shell type the following and find the ethernet IP address:

```shell
ip a
```

In my case, the IP that was selected is `192.168.3.212`.  From a web browser enter that address into the URL bar. For example:

`https://192.168.3.212`

### Create a user account.
You have the option of creating a user account and password. In my case, I set up a user called `hmuser`.

### Go to the Dashbaord
Click the `dashboard` link to continue to the dashboard of the portal.

### Adding a hard drive to Zima from the Dashboard
The next step is to format and add the hard drives we connected to the the Zima.

From the main Dashboard screen, click the settings `gear` in the `Storage` portlet. This should bring up
a storage configuration popup.

- Click `Storage` from the left-hand menu
- Click the `Start` button in the `Create Storage` section in the main panel.
- Click the `Combine use` to set up a RAID array or click `Single use` to set up individual disks. (NOTE: I'm using a RAID 0 for my exxample.)
- For RAID, click the drop-down arrow next to "RAID1"
- You should now see the option for `RAID0`. Click the radio button, then the `Next` button
- Select all the disk used for the RAID (two in my case), then click the `Next` button
- For `Storage name`, create a name for the shared drive. In my case I will call this `model-storage`
- Click the `I am aware of this and confirm the operation` checkbox, then click `Create`

Now the drives will be formatted into a RAID-0 array. This will take a few minutes.

>(IMPORTANT! RAID-0 has no redundancy so make sure the data you're storing here isn't important. In my case, I'll just
> be storing publicly available LLM models. So, I'm not worried if anything happens to the data. My goal is to just make
> the largest share possible from all the available drives.)

### Locating SMB connection information
Now that the drive is created, let's find the SMB share connection information. We'll need this when connecting
from my DGX spark devices.

From the main Dashboard screen, click the large `Files` icon.

- Click the `Shared` button on the upper left-hand menu
- Select `Share via Samba` at the top of the main panel
- Click the three dots (manage share) on the far right-hand side of the share you created in the last section `model-storage`
- You should see details about using the shared SMB drive here. The URL in the `macOS Finder` will be used for Ubuntu (DGX Spark)
- You will also have the option of adding a Share drive user at the bottom, along with permissions.
- Click `Save` when you're done.

## Connecting to the SMB Share
In this section I will assume you're connecting to the Shared drive using a DGX spark or other Ubuntu device.

### Setting up SMB on Ubuntu
First, let's verify that SMB is set up and running. Run the following commands:

```shell
### Test to see if CIFS is installed
mount.cifs -V

# You should see something like this:
# mount.cifs version: 7.0
```

If CIFS isn't installed, run the following commands:
```shell
sudo apt update
sudo apt install cifs-utils
```

### Creating a mount point
We'll need to create a drive for mounting the SMB share, on the DGX sparks. Run this command on all Sparks:

```shell
sudo mkdir -p /mnt/zima-llm-model
sudo chown hmuser /mnt/zima-llm-model
```

### (Option #1) Mount the Share manually
>(NOTE: Use the IP address and user info you gathered from the `Manage Share` from the Zima dashboard, mentioned above.)

>(IMPORTANT!!!! The `uid` and `gid` should be related to the user who has access to this share)

```shell
sudo mount -t cifs -o username=hmuser,uid=1000,gid=1000,password=myPassword,rw //192.168.3.212/model-storage /mnt/zima-llm-model
```


### (Option #2) Mount the Share automatically at startup
First, create a credentials file:

```shell
sudo vi /etc/smb-credentials
```

This should contain the following:
```text
username=hmuser
password=myPassword
```

Next, lock down permissions on the file:
```shell
sudo chmod 600 /etc/smb-credentials
```

Now edit the Fstab file:
```shell
sudo vi /etc/fstab
```

The contents should look something like this:
```bash
#### NOTE: Put these lines at the end of the file
# Add an SMB shared drive for LLM Models
//192.168.3.212/model-storage /mnt/zima-llm-model cifs credentials=/etc/smb-credentials,iocharset=utf8,uid=1000,gid=1000,file_mode=0770,dir_mode=0770,vers=3.0,x-systemd.automount,x-systemd.idle-timeout=60,nofail 0 0
```

### Change the Hugginface home directory
First create a hugging face cache folder in your shared drive:

```shell
mkdir -p /mnt/zima-llm-model/hf/cache
```

Add the following lines to the bottom of your `~/.bashrc` file
```shell
# If the SMB shared folder exists, change the Huggingface home environment variable
# This will change the default location where LLM Models are saved and read.
if [ -d "/mnt/zima-llm-model/hf/cache" ]; then
  export HF_HOME="/mnt/zima-llm-model/hf/cache"
fi
```

### Download a model to the shared folder 
>(NOTE: I'm assuming you already have the huggingface CLI installed) 

>(IMPORTANT!!! Make sure the `HF_HOME` environment variable was set from the last step, first!!!)

```shell
hf download local-inference-lab/Qwen3.8-Flash-Next-NVFP4
```

### Set the model folder to read-only 
>(IMPORTANT!!! If you don't set the model folder to read only, it's possible that a script like `run-recipe.sh` could try to
> download the model again causing corruption.)

Once a model has been successfully downloaded, it's a good idea to set that folder to `read-only`. To do that run the following command:

```shell
cd /mnt/zima-llm-model/hf/cache/hub
chmod -R 444 <MODEL_NAME_DIRECTORY>
## For example:
chmod -R 444 models--local-inference-lab--Qwen3.8-Flash-Next-NVFP4

```
