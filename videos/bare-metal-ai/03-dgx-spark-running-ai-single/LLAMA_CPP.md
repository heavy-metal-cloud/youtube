# Installation of llama.cpp for Nvidia Spark DGX devices
This document describes how to install llama.cpp from source so that it will
run on a Spark DGX devices utilizing the graphics card and CUDA

>(REFERENCE:
> - [https://forums.developer.nvidia.com/t/tutorial-build-llama-cpp-from-source-and-run-qwen3-235b/352604](https://forums.developer.nvidia.com/t/tutorial-build-llama-cpp-from-source-and-run-qwen3-235b/352604))


## Installation and Setup
### Clone the repo from Github and build
```shell
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

## Build for CUDA
cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=ON
cmake --build build --config Release -j 20
```

### Rebuild from source
To update to the latest llama.cpp, perform the following steps.

```shell
### Important!!! you should already be one level below the `llama.cpp` directory

git pull
cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=ON
cmake --build build --config Release -j 20
```

### Download some GGUF models
>(NOTE: This assumes you already have the huggingface CLI installed `hf`)

>(NOTE 2: These models will be downloaded to your Huggingface cache folder. Located here: `~/.cache/huggingface/hub`
> for example: `~/.cache/huggingface/hub/models--unsloth--Qwen3.6-35B-A3B-GGUF/snapshots/a483e9e6cbd595906af30beda3187c2663a1118c/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`)

>(IMPORTANT!!! If you are downloading a large model, it may be split into multiple GGUF files. In that case, you will have
> to use the `llama-gguf-split --merge` command. See the Nemotron 3 Super example below.)

```shell
### Download Nemotron 3 Super
hf download bartowski/nvidia_Nemotron-3-Super-120B-A12B-GGUF \
--include "nvidia_Nemotron-3-Super-120B-A12B-Q4_K_M/*"

### Merge split GGUF files into one
./llama-gguf-split --merge ./"nvidia_Nemotron-3-Super-120B-A12B-Q4_K_M-00001-of-00003.gguf ./"nvidia_Nemotron-3-Super-120B-A12B-Q4_K_M.gguf

### Download Qwen3.6-35B-A3B
hf download palmfuture/Qwen3.6-35B-A3B-GPTQ-Int4 
```

### Run llama.cpp as a CLI
```shell
cd build/bin

### Run the inference client
./llama-cli --no-mmap --ctx-size 32768 \
    --model /path/to/models/my-model.gguf
```

### Run llama.cpp as a service
**Qwen3.6-35B-A3B**

```shell
cd build/bin
./llama-server \
  --model  ~/.cache/huggingface/hub/models--unsloth--Qwen3.6-35B-A3B-GGUF/snapshots/a483e9e6cbd595906af30beda3187c2663a1118c/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 30000 \
  --n-gpu-layers 99 \
  --ctx-size 32000 \
  --reasoning-format auto \
  --threads 8
```

**Nemotron 3 Super**

```shell
cd build/bin
./llama-server \
  --model  ~/.cache/huggingface/hub/models--bartowski--nvidia_Nemotron-3-Super-120B-A12B-GGUF/snapshots/3aa25691977903b99c15280b71b0fe4860f05bfa/nvidia_Nemotron-3-Super-120B-A12B-Q4_K_M/nvidia_Nemotron-3-Super-120B-A12B-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 30000 \
  --n-gpu-layers 99 \
  --flash-attn on \
  --ctx-size 16384 \
  --reasoning-format auto \
  --threads 8

```

## Clients
### Continue Plugin for VSCode
If you're using the VSCode plugin "Continue", you can set up your `config.yaml` file to look something like this:

```yaml
name: Local Config
version: 1.0.0
schema: v1
models:
    
  - name: LLAMA-Qwen3.6-35B-A3B-UD-Q4_K_M
    provider: openai
    model: Qwen/Qwen3.6-35B-A3B-UD-Q4_K_M
    apiBase: http://192.168.3.210:30000/v1
    defaultCompletionOptions:
      temperature: 0.8
      contextLength: 200000
      maxTokens: 150000
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
```

