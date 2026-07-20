# Connecting Two DGX Spark-style devices
Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

This document walks through the process of connecting two DGX Spark devices together. In my case, I will be using the
following hardware:

- Gigabyte AI Top Atom
- Asus Ascent GX-10
- ASUS Ascent GX10 0.4m 400G QSFP112 DAC Cable (Direct connection between both GB-10 devices)

## Using the Nvidia Playbook
For this document I will be using the Manual address allocation in the Nvidia playbook listed below:

- [https://build.nvidia.com/spark/connect-two-sparks/stacked-sparks](https://build.nvidia.com/spark/connect-two-sparks/stacked-sparks)

### Verify you have the same user on both machines
In my case I have a user called `hduser` on both machines with the same password

If you don't have a shared user, the playbook recommends and `nvidia` user.

>(NOTE: This is optional if you already have the same user on both machines.)

```shell
# Create nvidia user and add to sudo group
sudo useradd -m nvidia
sudo usermod -aG sudo nvidia

# Set password for nvidia user
sudo passwd nvidia

# Switch to nvidia user
su - nvidia
```

### Connect the QSFP112 Cable and verify connectivity
>(IMPORTANT!!! Make sure you connect the cable to the SAME side of both machines. I'm using the 'left' NIC on both GB-10 devices
> when looking from the back. The 'left' NIC seems to be the first port. So, it's a good one to choose)

Connect your QSFP cable to the same side of both machines.

Now test that the connection is working. Shell into both machines and run the following command:

```shell
ibdev2netdev
```

You should see something like this. Note that two logical interfaces are `Up`:
``` 
rocep1s0f0 port 1 ==> enp1s0f0np0 (Up)
rocep1s0f1 port 1 ==> enp1s0f1np1 (Down)
roceP2p1s0f0 port 1 ==> enP2p1s0f0np0 (Up)
roceP2p1s0f1 port 1 ==> enP2p1s0f1np1 (Down)
```

### Configure the networks and IP addressing for each node
In my case, the Gigabyte will be considered `Node 1` and the Asus will be `Node 2`.

**Node 1**
```shell
# Create the netplan configuration file
sudo tee /etc/netplan/40-cx7.yaml > /dev/null <<EOF
network:
  version: 2
  ethernets:
    enp1s0f0np0:
      addresses:
        - 192.168.100.10/24
      dhcp4: no
    enp1s0f1np1:
      addresses:
        - 192.168.200.12/24
      dhcp4: no
    enP2p1s0f0np0:
      addresses:
        - 192.168.100.14/24
      dhcp4: no
    enP2p1s0f1np1:
      addresses:
        - 192.168.200.16/24
      dhcp4: no
EOF

# Set appropriate permissions
sudo chmod 600 /etc/netplan/40-cx7.yaml

# Apply the configuration
sudo netplan apply

```

**Node 2**
```shell
# Create the netplan configuration file
sudo tee /etc/netplan/40-cx7.yaml > /dev/null <<EOF
network:
  version: 2
  ethernets:
    enp1s0f0np0:
      addresses:
        - 192.168.100.11/24
      dhcp4: no
    enp1s0f1np1:
      addresses:
        - 192.168.200.13/24
      dhcp4: no
    enP2p1s0f0np0:
      addresses:
        - 192.168.100.15/24
      dhcp4: no
    enP2p1s0f1np1:
      addresses:
        - 192.168.200.17/24
      dhcp4: no
EOF

# Set appropriate permissions
sudo chmod 600 /etc/netplan/40-cx7.yaml

# Apply the configuration
sudo netplan apply

```

### Setting up password-less SSH
To allow machine-to-machine communication without passwords, you'll have to copy the public SSH keys from
each machine over.

To Automatically perform server discovery, run the following script:

>(NOTE: You will be prompted for your password a few times.)

```shell
curl -O https://raw.githubusercontent.com/NVIDIA/dgx-spark-playbooks/refs/heads/main/nvidia/connect-two-sparks/assets/discover-sparks
chmod +x discover-sparks
./discover-sparks
```

### Verify SSH connectivity across nodes
You should now be able to ssh into each other node without a password.  If you followed the playbook instructions you
can test this using the following commands

```shell
### From Node 1
ssh 192.168.100.11

### From Node 2
ssh 192.168.100.10
```

## Setting up NVIDIA Collective Communication Library (NCCL)
>(REFERENCE:
> - [https://build.nvidia.com/spark/nccl/overview](https://build.nvidia.com/spark/nccl/overview))

Now that both Spark machines are connected, it's time to set up NCCL which will allow for GPU-to-GPU communication.
I will be following the playbook listed above.

### Build NCCL with Blackwell support
Run the following command to build NCCL on each machine

```shell
# Install dependencies and build NCCL
sudo apt-get update && sudo apt-get install -y libopenmpi-dev
git clone -b v2.28.9-1 https://github.com/NVIDIA/nccl.git ~/nccl/
cd ~/nccl/
make -j src.build NVCC_GENCODE="-gencode=arch=compute_121,code=sm_121"

# Set environment variables
export CUDA_HOME="/usr/local/cuda"
export MPI_HOME="/usr/lib/aarch64-linux-gnu/openmpi"
export NCCL_HOME="$HOME/nccl/build/"
export LD_LIBRARY_PATH="$NCCL_HOME/lib:$CUDA_HOME/lib64/:$MPI_HOME/lib:$LD_LIBRARY_PATH"
```

### Build the Test suite
```shell
# Clone and build NCCL tests
git clone https://github.com/NVIDIA/nccl-tests.git ~/nccl-tests/
cd ~/nccl-tests/
make MPI=1
```

### Find the active IP address for each machine

From each machine run the following:
```shell
ibdev2netdev
```

You should see something like this:
``` 
rocep1s0f0 port 1 ==> enp1s0f0np0 (Up)
rocep1s0f1 port 1 ==> enp1s0f1np1 (Down)
roceP2p1s0f0 port 1 ==> enP2p1s0f0np0 (Up)
roceP2p1s0f1 port 1 ==> enP2p1s0f1np1 (Down)
```

Next, run this command:
```shell
ip addr show enp1s0f0np0
```

Which should produce something like this:
>(NOTE: That in this case, the IP address is: `192.168.100.10`, do this for both machines!)
``` 
13: enp1s0f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 48:21:0b:96:06:06 brd ff:ff:ff:ff:ff:ff
    inet 192.168.100.10/24 brd 192.168.100.255 scope global noprefixroute enp1s0f0np0
       valid_lft forever preferred_lft forever
    inet6 fe80::4a21:bff:fe96:606/64 scope link
       valid_lft forever preferred_lft forever
```

In my case, the IP addresses are as follows:
- **Node 1** - 192.168.100.10
- **Node 2** - 192.168.100.11

### Test NCCL Connectivity
To test, run the following command on both machines:
```shell
# Set network interface environment variables (use your Up interface from the previous step)
export UCX_NET_DEVICES=enp1s0f0np0
export NCCL_SOCKET_IFNAME=enp1s0f0np0
export OMPI_MCA_btl_tcp_if_include=enp1s0f0np0

# Run the all_gather performance test across both nodes (replace the IP addresses with the ones you found in the previous step)
mpirun -np 2 -H 192.168.100.10:1,192.168.100.11:1 \
  --mca plm_rsh_agent "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" \
  -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH \
  $HOME/nccl-tests/build/all_gather_perf
  
  
### Larger test (200 Gb/s)

# Run the all_gather performance test across both nodes
mpirun -np 2 -H 192.168.100.10:1,192.168.100.11:1 \
  --mca plm_rsh_agent "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" \
  -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH \
  $HOME/nccl-tests/build/all_gather_perf -b 16G -e 16G -f 2
```

## Downloading and moving models
I've found it's best to download the models locally first into the huggingface cache folder. You should perform this
on one server then `tar` the file into an archive and copy it over to the other server.

```shell
### Download the file from hugging face
### (NOTE: You can use 'includes' and 'excludes' to make the model download faster
hf download openai/gpt-oss-120b  --exclude "original/*" --exclude "metal/*"

### Archive the file for easy transport
cd  ~/.cache/huggingface/hub
tar cvf  models--openai--gpt-oss-120b.tar models--openai--gpt-oss-120b/

### Use Rsync to move the file. This is more efficient when using ConnectX-7, since it doesn't have the 
### CPU overhead of `scp`
rsync -ahP --no-compress -e 'ssh -T -c aes128-ctr' \
  /home/hmuser/.cache/huggingface/hub/models--openai--gpt-oss-120b.tar \
  hmuser@192.168.100.194:/home/hmuser/.cache/huggingface/hub/
```

Next, ssh into the other server and run the following command:
```shell
cd /home/hmuser/.cache/huggingface/hub/
tar -xvf models--openai--gpt-oss-120b.tar
rm models--openai--gpt-oss-120b.tar
```

## Running models using vLLM (eugr docker image)
>(REFERENCE: [https://github.com/eugr/spark-vllm-docker](https://github.com/eugr/spark-vllm-docker))

At this time, this seems to be the preferred way of running models on multiple GB-10 devices. I'm having some issues getting
Sparkrun to work correctly. This is a little odd, since sparkrun leverages the eugr images for vLLM.

### Build the eugr docker image for vLLM
```shell
### Optional, create a directory for vLLM and `cd` into it. Mine will live under `~/llm`
cd ~/llm

git clone https://github.com/eugr/spark-vllm-docker.git
cd spark-vllm-docker

# If you're running a cluster of GB-10 devices, use this command instead!
./build-and-copy.sh -c
```

### Run the `autodiscover` script to set up all GB-10 servers
>(NOTE: This will create a `.env` file in the current directory)
```shell
# NOTE: You should already be in the `spark-vllm-docker` folder from the previous step
./autodiscover.sh
```

### Download a model
You can either manually download the model using the HuggingFace CLI mentioned above, or you can use the
following utility listed below:
```shell
# Here's an example using the MiniMax M2.7 model
./hf-download.sh cyankiwi/MiniMax-M2.7-AWQ-4bit -c --copy-parallel
```

### Running a model using a recipe
```shell
# NOTE: You should already be in the `spark-vllm-docker` folder from the previous step
./run-recipe.sh nemotron-3-super-nvfp4

# Or
./run-recipe.sh 
```



## Running models with Sparkrun
We will use Sparkrun to serve LLM models using 2 GB-10 devices. I'm assuming you've already installed Sparkrun using
the following instructions:
- [./SPARK_RUN.md](./SPARK_RUN.md)

### Install Python dependencies
I had to update the following dependencies due to the following error when running vLLM:
`[ray_utils.py:89] AttributeError: 'MergedColumnParallelLinear' object has no attribute 'orig_dtype'`

```shell
pip install --upgrade vllm ray
```

### Configure sparkrun to use to GB-10 devices
```shell
sparkrun setup wizard
```

Use the following settings:
``` 
Continue with this cluster? [Y/n]: n

## In this case, the IP addresses of my 10Gb ethernet ports are 192.168.3.220 (node 1) and 192.168.3.221 (node 2)
Enter host IPs/hostnames (comma-separated) [192.168.3.220]: 192.168.3.220,192.168.3.221

## You can enter any name here
Cluster name [default]: 2spark

SSH username [hmuser]:

Set up SSH mesh across 2 host(s) + this machine? [Y/n]: Y

Configure CX7 networking? [Y/n]: Y

Add 'hmuser' to the docker group on all hosts? [Y/n]: Y

Install sudoers entries? [Y/n]: Y

Install earlyoom? [Y/n]: Y
```

### Saving a recipe
In this case I will be using the GPT-OSS-120B recipes for 2 nodes from Spark-arena:

>(REFERENCES:
> - [https://spark-arena.com/leaderboard](https://spark-arena.com/leaderboard)
> - `curl -o recipe.yaml https://spark-arena.com/api/recipes/7a5a73cb-96d0-46bc-a02c-9d0d46523bdd/raw`)


Below is the recipe which can be saved to a file called `gpt-oss-120b-2_node-MXFP4-vllm.yaml`:
```yaml
build_args:
  - '--exp-mxfp4'
container: vllm-node-mxfp4
env:
  VLLM_USE_FLASHINFER_MOE_MXFP4_MXFP8: '1'
command: |
  vllm serve openai/gpt-oss-120b \
      --tool-call-parser openai \
      --reasoning-parser openai_gptoss \
      --enable-auto-tool-choice \
      --tensor-parallel-size {tensor_parallel} \
      --distributed-executor-backend ray \
      --gpu-memory-utilization {gpu_memory_utilization} \
      --enable-prefix-caching \
      --load-format fastsafetensors \
      --quantization mxfp4 \
      --mxfp4-backend CUTLASS \
      --mxfp4-layers moe,qkv,o,lm_head \
      --attention-backend FLASHINFER \
      --kv-cache-dtype fp8 \
      --max-num-batched-tokens {max_num_batched_tokens} \
      --host {host} \
      --port {port}
cluster_only: false
name: OpenAI GPT-OSS 120B
mods: []
model: openai/gpt-oss-120b
defaults:
  port: 8000
  max_num_batched_tokens: 8192
  gpu_memory_utilization: 0.7
  tensor_parallel: 2
  host: 0.0.0.0
description: vLLM serving openai/gpt-oss-120b with MXFP4 quantization and FlashInfer
recipe_version: '1'
solo_only: false

```

### (OPTIONAL) Use a local model only!  Prevent hugging face from using a remote model
>(NOTE: If you manually downloaded the model to all GB-10 servers using the HuggingFace CLI, you can use this command to
> prevent HF from trying to grab the remote model. This comes in handy when you have a model like GPT-OSS-120B with a large
> number of variants that bloat the model size. This way you can use just the model you downloaded using the `--excludes` option.)

```shell
# Prevents libraries (like Hugging Face Transformers/vLLM) from trying to connect to the internet to verify or download models
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
```

### Running the recipe file
```shell
sparkrun run gpt-oss-120b-2_node-MXFP4-vllm.yaml
```




## Troubleshooting
### Common Networking and PCIe commands
```shell
ibdev2netdev

lspci
## Tree view
sudo lspci -tv
## Show all devices and PCIe width
sudo lspci -nnvv | grep -E "^[0-9a-fA-F]|^[[:space:]]+LnkSta:"

### All PCIe device info (NOTE: VERY Verbose output!!!!)
sudo lspci -vvv

ip a
ip -br a

netplan status

nvidia-smi


ib_send_bw

rdma link
ibv_devices

### Install the Infiniband tooling
sudo apt install infiniband-diags
ibstats


```


## Reverting back / Cleanup
To revert back to a Single GB-10 device and remove the ConnectX-7 IP's run the following commands from each machine:

```shell
# Rollback network configuration (if using Option 1)
sudo rm /etc/netplan/40-cx7.yaml
sudo netplan apply
```