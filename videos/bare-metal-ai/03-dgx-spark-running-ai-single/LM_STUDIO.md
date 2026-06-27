# Installation of LM Studio on Nvidia Spark DGX devices
This document describes how to install LM Studio onto a Spark DGX Device

>(REFERENCE:
> - [https://forums.developer.nvidia.com/t/tutorial-build-llama-cpp-from-source-and-run-qwen3-235b/352604](https://forums.developer.nvidia.com/t/tutorial-build-llama-cpp-from-source-and-run-qwen3-235b/352604))


## Installation and Setup
### Download the executable
>(IMPORTANT!!! Make sure to select `Arm64` from the "running" dropdown box! )
Navigate to the following webpage and download the appropriate executable:

- [https://lmstudio.ai/download?arch=arm64&version=0.4.12](https://lmstudio.ai/download?arch=arm64&version=0.4.12)

### Running the executable
You should now have a file that looks like `LM-Studio-0.4.12-1-arm64.AppImage` in your `~/Downloads` directory.

From a shell run the following commands:
```shell
cd ~/Downloads
./LM-Studio-0.4.12-1-arm64.AppImage --no-sandbox
```

### Running LM Studio
At this point, LM Studio should have launced. You can now download and run models as you normally would. The Server should be working, as well, for remote access to the model.

### Running LM Studio as a Server
In LM Studio, perform the following steps to run a model as a server, this would be similar to the way `vLLM` works.

- click the `Developer` tab on the left-hand side.
- At the top, click the `server settings` button
- Click the `Serve on local network` slider button. (This will allow LM Studio to advertise your ethernet IP)
- Click the `+ Load Model` button

At this point, the server should be running. You will need a client (agent, etc) to access the server. (see below for `continue` plugin instructions)

### Configue the `Continue` VSCOde plugin to access LM Studio
Assuming you already have LM Server hosting a model, you can set up `Continue`
to access the model remotely.

>(NOTE: For more details about running LM Studio with the Continue plugin, check out this README file: [../LLM_TOOL_SETUP.md](../LLM_TOOL_SETUP.md))

With the `Continue` plugin installed in VS Code, select the plugin then perform the following:

From the Plugin menu, click:

**Config** - From the left-hand menu
- Click `Local Config`

You should be prompted with a yaml file called `config.yaml` update
the file to look something like this, to configure your remote model:

```yaml
name: Local Config
version: 1.0.0
schema: v1
models:
  - name: GPT OSS 120B Mac Studio
    provider: lmstudio
    model: openai/gpt-oss-120b
    apiBase: http://192.168.3.23:1234/v1
    defaultCompletionOptions:
      temperature: 0.7
      contextLength: 100000
    roles:
      - chat
      - apply
      - edit
    capabilities:
      - tool_use
```