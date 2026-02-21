# This document walks through setting up the tooling for a bare metal LLM.
In this case I will be using a Mac Studio. However, you could use a Macbook pro or a server
with Nvidia / AMD GPUs instead.

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

## LM Studio
LM Studio is a GUI based tool for loading LLMs

### Download and install
Download the latest version at:
- [https://lmstudio.ai/](https://lmstudio.ai/)

Once LM Studio is installed, you will be prompted with a setup
wizard. Select the following options:

- **Choose Your Level** - `Developer` will give you full functionality and access
- **Enable local LLM service on startup** - You can check this
- Click `skip` to bypass the model they're recommending (Ex: gpt-oss-20b)

### Download a model
From the left-hand menu, click the `Discover` button. It will look like a magnifying glass.

>(NOTE: In my case I will be downloading a large model called `gpt-oss-120b`, you should select a model
> that will run on your computer)

Search for `gpt-oss-120b`

### Expose the model as a service
To expose your model as a service select the following:

From the left-hand menu, select **Developer**

Click `Server Settings`
- **Serve on Local Network** - This should be enabled

Next click the slider to start the server.

Assuming your server has an IP address of `192.168.3.23`, then the service would be accessible
from:
- [http://192.168.3.23:1234/v1](http://192.168.3.23:1234/v1)

## Setting up VS Code to access the Remote LLM
With the LLM running a model, you can now access it from a remote computer.

>(REFERENCES:
> - [https://www.continue.dev/](https://www.continue.dev/)
> - [https://docs.continue.dev/reference](https://docs.continue.dev/reference)
> - [https://docs.continue.dev/ide-extensions/agent/how-it-works](https://docs.continue.dev/ide-extensions/agent/how-it-works))

Install the following plugin: `continue`

### Configure the Continue Plugin
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
      # contextLength: 100000
    roles:
      - chat
      - apply
      - edit
    capabilities:
      - tool_use

  - name: devstral-small-2-2512
    provider: lmstudio
    model: mistralai/devstral-small-2-2512
    apiBase: http://192.168.3.23:1234/v1
    defaultCompletionOptions:
      temperature: 0.7
      contextLength: 393216
    roles:
      - chat
      - apply
      - edit
    capabilities:
      - tool_use
      - image_input

  - name: Qwen2-5-Coder-14-B-Mac-Studio
    provider: lmstudio
    model: qwen/qwen2.5-coder-14b
    apiBase: http://192.168.3.23:1234/v1
     defaultCompletionOptions:
       temperature: 0.7
       #maxTokens: 32000
       contextLength: 100000
    roles:
      - autocomplete
    capabilities:
      - tool_use
    requestOptions:
      extraBodyProperties:
        think: false  # turning off the thinking

```

At this point you should be able to start a new chat and get results back.

### Load a recursive sub-directory into context
From the `Continue` plugin prompt, you can type something like this
to load in a whole directory:

```
@tree Describe the contents of this directory
```

>(REFERENCE: [https://docs.continue.dev/customize/deep-dives/custom-providers#@tree](https://docs.continue.dev/customize/deep-dives/custom-providers#@tree))

### Creating files in Agent mode
Once the model is running, you will have the option to create files.

>(IMPORTANT!!! Files can only be created in a `trusted` repository (folder) that is currently opened
> in VSCode. All files will be created relative to this location.)

In the dropdown for the model chat, select `agent mode`. Now in the chat you can
use terms like `create_new_file` to create a new file.  Detailed instructions can be
found here:

- [https://docs.continue.dev/ide-extensions/agent/how-it-works](https://docs.continue.dev/ide-extensions/agent/how-it-works)

### Autocomplete
To use autocomplete, make sure you're using a model that's capable of this functionality, for example
`qen2.5-coder-14b`

Your config file in the VS Code Continue plugin should look something like this for that model:

>(NOTE: The important part here is the `role` of the model that's set to `autocomplete`)

```yaml
name: Local Config
version: 1.0.0
schema: v1
models:
  - name: Qwen2-5-Coder-14-B-Mac-Studio
    provider: lmstudio
    model: qwen/qwen2.5-coder-14b
    apiBase: http://192.168.3.23:1234/v1
     defaultCompletionOptions:
       temperature: 0.7
       #maxTokens: 32000
       contextLength: 100000
    roles:
      - autocomplete
    capabilities:
      - tool_use
    requestOptions:
      extraBodyProperties:
        think: false  # turning off the thinking

```