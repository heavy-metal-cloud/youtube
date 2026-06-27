# Install ComfyUI onto an Ubuntu server
These instructions install ComfyUI onto an Ubuntu server. In my case, this will be an Nvidia DGX Spark-style
device.

>(REFERENCES:
> - [https://comfy.org/](https://comfy.org/)
> - [https://github.com/comfy-org/comfyui](https://github.com/comfy-org/comfyui)
    >)

## Installation and Setup
For Ubuntu we will be using the Github installation instructions.

>(NOTE: You should already have Python installed with a virtual environment selected)

### (OPTIONAL) Create a Python environment
```shell
cd ~
python3 -m venv myenv
```

### Use the environment
```shell
source ~/myenv/bin/activate
```

### Install the ComfyUI CLI
```shell
pip install comfy-cli
comfy install
```

>(NOTE: ComfyUI will be installed at the following location: `~/comfy/ComfyUI`)

### Install CustomUI Manager to install custom Nodes
First run this from your Python environment:

```shell
pip install -U --pre comfyui-manager
```

### Set Security to Weak to allow for manager installation of Nodes, etc.
Edit the following file `~/comfy/ComfyUI/user/__manager/config.ini`:

```
security_level = weak
network_mode = personal_cloud
```

>(NOTE: You can set `security_level = normal`  and `network_mode = public` once you've installed your custom nodes, etc.)

### Starting ComfyUI
```shell
cd ~/comfy/ComfyUI

python main.py --enable-manager --listen 0.0.0.0
```

### Running ComfyUI
ComfyUI is a web app and can now be access from a web browser using port `8188`

For example, if my IP address is "192.168.3.210", then I would use the following URL:

http://192.168.3.210:8188

This is nice because you can use your DGX box as a headless device while rendering AI images remotely from your
desktop.


### Installing a custom Node from ComfyUI
In this case we will install the `comfyui-text-randomizer` node.

- Click the UpperCase `C` menu item
- Click `Extensions`
- Search for "comfyui-text-randomizer"
- Cick `Install`
- Click `Apply Changes`
