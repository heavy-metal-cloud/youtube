# Host Your Own AI - DGX Spark
Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

This document walks through the process of setting up a DGX Spark-style device.

## Initial Boot up
### Setting up the hardware
You will need to set up a Bluetooth/USB-c keyboard and mouse

### Timezone
Set up your local timezone. (In my case this is EST)

### Select the Keyboard language and layout
In my case this is English (US)

### Create a user account
Here's an example I'm using:

- **Create Username** - I'm using `hmuser`, but create your own user account
- **Create Password** - Create a secret password here
- **Confirm Password** - Verify your password

### Send statistics to Nvidia
You can choose to send analytics and crash data to Nvidia

### Set up your WIFI
Select your local wifi, if you have one and enter the password for the WIFI router.

### Installing Updates
At this point your devices should begin installing the latest updates.

## Nvidia Sync for remote connections
I like to run the GB-10 devices as a headless server. To make this easier, you should install the Nvidia Sync application
on your client computer. This will allow you to easily SSH into your server and view the DGX Dashboard.

Installation instructions are below:
- [https://build.nvidia.com/spark/connect-to-your-spark/sync](https://build.nvidia.com/spark/connect-to-your-spark/sync)
- [https://docs.nvidia.com/dgx/dgx-spark/nvidia-sync.html](https://docs.nvidia.com/dgx/dgx-spark/nvidia-sync.html)


## Post Boot-up configuration and installation
>(NOTE: I will be running the following steps from a Terminal on a Macbook pro accessing the GB-10 device as a server, using the Nvidia
> Sync application)

Using the Nvidia Sync command, open a terminal session to your GB-10 device and run the following commands to set up your
server.

### Add your user to the docker group
To run docker without being root, you will have to update your group membership to include `docker`

```shell
sudo usermod -aG docker $USER
newgrp docker
```

### Installing Homebrew
To install brew, you should follow the linux installation instructions.

```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

### add Brew to your path
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
```

Test that Brew is running:
```shell
brew --help
```

### Install `uv` for Python
UV is a rust-based utility for Python.

>(REFERENCE: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/))

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh

### Optional installation
### You could use brew instead, like this:
###
### brew install uv
```

To add UV to your path, add the following line to your `~/.bashrc` file:
>(NOTE: If you used `brew` to install `uv`, you can skip this step!)

```
. "$HOME/.local/bin/env"
```

### Create a Python environment
```shell
cd ~
python3 -m venv myenv
```

Use the environment
```shell
source ~/myenv/bin/activate
```

### (OPTIONAL) Source the `myenv` during startup
Instead of issuing the command above all the time, you can just add it to your startup scripts.

Add the following line to the bottom of the startup file: `~/.bashrc`

```shell
echo '. "$HOME/myenv/bin/activate"' >> ~/.bashrc
```

### (OPTIONAL) Install Python compile headers
If you will be training models using `torch compile`, you will have to run the following command to install
the python compile headers.

```shell
sudo apt-get install python3-dev
```

### (OPTIONAL) Install the Hugging Face CLI
>(REFERENCE: [https://huggingface.co/docs/huggingface_hub/en/guides/cli](https://huggingface.co/docs/huggingface_hub/en/guides/cli))

```shell
curl -LsSf https://hf.co/cli/install.sh | bash
```

To verify the install worked, run the following command. This is also useful for viewing the models that vLLM installed on your machine:

```shell
hf cache list
```

### (OPTIONAL) Install Rust
```shell
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
## Open a new shell or re-source your ~/.bashrc
rustup toolchain install nightly
```

### (OPTIONAL) Change the UI time from military time to 12 Hour AM/PM
```shell
gsettings set org.gnome.desktop.interface clock-format '12h'
```

### Install Eugr's Docker container for vLLM
>(Reference:
> - [https://github.com/eugr/spark-vllm-docker](https://github.com/eugr/spark-vllm-docker) )

Detailed instructions are listed here: [VLLM.md](VLLM.md)

Create the Eugr docker container for the DGX.
>(NOTE: This is pretty important if you will be running Spark Run.)

```shell
### Optional, create a directory for vLLM and `cd` into it. Mine will live under `~/tmp`
mkdir ~/llm
cd ~/llm

git clone https://github.com/eugr/spark-vllm-docker.git
cd spark-vllm-docker

sudo ./build-and-copy.sh
```

### Install Spark Run 
>(REFERENCE: [https://github.com/spark-arena/sparkrun](https://github.com/spark-arena/sparkrun))

Detailed instructions are listed here: [SPARK_RUN.md](SPARK_RUN.md)

## Running Applications on the GB-10
Nvidia's recommended starting point would be the playbooks for the DGX Spark

- [https://build.nvidia.com/spark](https://build.nvidia.com/spark)

For my personal use, I will be treating the GB-10 device as a headless server and an image/video rendering platform.
Agents and other clients will run either from a Kubernetes pod or a local workstation.

With this in mind, I recommend visiting the Spark Arena community site and installing the following two apps:

### The Spark Arena community
Spark Run is part of a great community and ecosystem from the Spark Arena web page.

Spark Arena is a website with models and configurations that have been tested and benchmarked on the DGX Spark:
>(REFERENCE: [https://spark-arena.com/](https://spark-arena.com/))

### Installing and running Sparkrun
Spark Run is an application that will automatically download the correct serving platform (ex: vLLM), download the model and
start serving it:

>(REFERENCE: [https://github.com/spark-arena/sparkrun](https://github.com/spark-arena/sparkrun))

To install Sparkrun, check out the following markdown instructions: [./SPARK_RUN.md](./SPARK_RUN.md)

### Installing and running ComfyUI for image and Video Rendering
The second application to install is ComfyUI. This will allow you to render images and video.

To install ComfyUI, check out the following markdown instructions: [./COMFY_UI.md](./COMFY_UI.md)


## Monitoring and troubleshooting
### Docker startup issues
If you're having trouble running docker, first check to see if it's a buildkit issue:

First check the journal for errors:
```shell
sudo journalctl -u docker.service -n 50 --no-pager
```

If you're encountering a buildkit issue, you'll see an error like the one below
```
error initializing buildkit: error creating buildkit instance: invalid database
```

To fix the issue, run the following commands:
```shell
sudo systemctl stop docker
sudo systemctl disable docker

sudo mv /var/lib/docker/buildkit /var/lib/docker/buildkit-bad

sudo systemctl enable docker
sudo systemctl start docker
```

### View CUDA versions
```shell
nvcc --version
```

### Cleanup
You'll start to accumulate large models. To find them for cleanup, run the following command:

```shell
sudo du -ahx / | sort -rh | head -50
```

### Clean the Docker build cache files
Every once in a while you should run the following commands to cleanup the docker build cache files:

```shell
### View the build cache size
docker system df

docker builder prune
```

### Pytorch version errors with Cuda
When using Pytorch you might run into the following error message:
```
/home/hmuser/jupyterlab/.venv/lib/python3.12/site-packages/torch/cuda/__init__.py:283: UserWarning: 
    Found GPU0 NVIDIA GB10 which is of cuda capability 12.1.
    Minimum and Maximum cuda capability supported by this version of PyTorch is
    (8.0) - (12.0)
    
  warnings.warn(
```

If you see this, then you will have to reinstall Pytorch with the latest version. If you don't do this
CUDA may fall back to using the CPU for processing which will cause massive slowdowns in training / fine-tuning.

To fix the issue run these commands from the terminal
```shell
pip uninstall torch torchvision torchaudio -y
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu130
```

If you're using a Jupyter notebook, you can also run the commands from a cell using the following:
```python
!pip uninstall torch torchvision torchaudio -y
!pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu130
```

### Stats including temperature
The DGX can get hot when the GPU and/or CPU are pegged. Here's a utility to show the current
temperature and power usage.

```shell
nvidia-smi
```

