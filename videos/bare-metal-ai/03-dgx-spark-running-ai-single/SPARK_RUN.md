# Spark Run instructions for the DGX Spark
Spark Run is a CLI that simplifies curated models and configurations across different serving platforms, like vLLM, SGLang, etc.

This allows you to quickly run recipes from the Spark Arena website: [https://spark-arena.com/leaderboard](https://spark-arena.com/leaderboard)

>(REFERENCES: 
> - [https://github.com/spark-arena/sparkrun](https://github.com/spark-arena/sparkrun)
> - [https://spark-arena.com/leaderboard](https://spark-arena.com/leaderboard))

## Installation and Set up
### Install
>(REFERENCE:
> - [https://github.com/spark-arena/sparkrun](https://github.com/spark-arena/sparkrun))

>(NOTE: Use the IP address or `localhost` for the machine name and leave the rest of the defaults as-is)

```shell
uvx sparkrun setup
```

>(IMPORTANT!!! If you only have a single DGX Spark, make sure (Phase 2) is set to "No"
> `Set up SSH mesh across 1 host(s) + this machine? [Y/n]: n`)

Here's an example output of the set up:
```
Phase 1: Cluster Setup
------------------------------
Enter DGX Spark host IPs/hostnames (comma-separated): localhost
Detecting CX7 on remote hosts...
Cluster name [default]:
SSH username [hmuser]:
Cluster 'default' already exists. Update it? [Y/n]: y
Updated cluster 'default'.

Phase 2: SSH Mesh
------------------------------
Set up SSH mesh across 1 host(s) + this machine? [Y/n]: n

Phase 4: Docker Group Membership
------------------------------
Ensures user can run Docker commands without sudo.
Add 'hmuser' to the docker group on all hosts? [Y/n]: y
  localhost: 'hmuser' already a member

Phase 5: Sudoers Entries
------------------------------
Scoped sudoers for fix-permissions + clear-cache (no broad sudo).
Install sudoers entries? [Y/n]: y
  fix-permissions: 1/1 host(s)
  clear-cache: 1/1 host(s)

Phase 6: earlyoom OOM Protection
------------------------------
Prevents system hangs by proactively managing memory pressure.
Install earlyoom? [Y/n]: y
  earlyoom configured on 1/1 host(s).


Setup Complete!
================================================
```

### Running Spark Run

```shell
### Show the recipes
sparkrun list

### Sort by a runtime (like vLLM)
sparkrun list --runtime vllm-distributed
```

```shell
# Run an inference workload
sparkrun run qwen3-1.7b-vllm

# Multi-node tensor parallelism (TP maps to node count on DGX Spark)
sparkrun run qwen3-1.7b-vllm --tp 2

# Re-attach to logs, stop a workload, check status
sparkrun logs qwen3-1.7b-vllm
sparkrun stop qwen3-1.7b-vllm
sparkrun status
```

## Clients
The default port of the running LLM server is `8000` it exposes an OpenAI standard endpoint

### Continue Plugin for VSCode
If you're using the VSCode plugin "Continue", you can set up your `config.yaml` file to look something like this:

```yaml
name: Local Config
version: 1.0.0
schema: v1
models:

  - name: SPARKRUN-qwen3-1.7b-vllm
    provider: openai
    model: qwen3-1.7b
    apiBase: http://192.168.3.210:8000/v1
    defaultCompletionOptions:
      temperature: 0.8
      contextLength: 30000
      maxTokens: 10000
    roles:
      - chat
      - apply
      - edit
    capabilities:
      - tool_use
      - image_input
    requestOptions:
      extraBodyProperties:
        chat_template_kwargs:
          enable_thinking: true


## Cleanup
To uninstall Spark Run, run the following commands:

```shell 
uv tool uninstall sparkrun

rm -rf ~/.sparkrun
rm -rf ~/.cache/sparkrun
```