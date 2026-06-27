# Installing vLLM on a Spark
>(NOTE: At this point it seems like the best installation for vLLM is via a docker container. See below)

## Installation and operation
### (Option 1): Eugr's Docker container
>(Reference: 
> - [https://github.com/eugr/spark-vllm-docker](https://github.com/eugr/spark-vllm-docker) )


```shell
### Optional, create a directory for vLLM and `cd` into it. Mine will live under `~/tmp`
cd ~/tmp

git clone https://github.com/eugr/spark-vllm-docker.git
cd spark-vllm-docker

./build-and-copy.sh

### OPTIONAL!!
# If you're running a cluster of GB-10 devices, use this command instead!
# ./build-and-copy.sh -c
```

### Running a model as a service
>(NOTE: The service will be running on port 8000)

>(IMPORTANT!!: Models are stored by default at the following directory: `~/.cache/huggingface/hub`.  This is useful if you need to clean up older models)

**Default Model**
```shell
./launch-cluster.sh --solo exec \
  vllm serve \
    QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ \
    --port 8000 --host 0.0.0.0 \
    --gpu-memory-utilization 0.7 \
    --load-format fastsafetensors
    
```

### Downloading a model from hugging face and running it via vllm serve
>(NOTE: This assumes you already have the huggingface CLI installed `hf`)

>(NOTE 2: These models will be downloaded to your Huggingface cache folder. Located here: `~/.cache/huggingface/hub`
> for example: `~/.cache/huggingface/hub/models--unsloth--Qwen3.6-35B-A3B-GGUF/snapshots/a483e9e6cbd595906af30beda3187c2663a1118c/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`)

```shell
hf download palmfuture/Qwen3.6-35B-A3B-GPTQ-Int4

source ~/myenv/bin/activate

# This will vary based on your installation. Mine is in `export VLLM_HOME=~/tmp/spark-vllm-docker`
cd $VLLM_HOME  

./launch-cluster.sh --solo exec \
  vllm serve \
    palmfuture/Qwen3.6-35B-A3B-GPTQ-Int4 \
    --port 8000 --host 0.0.0.0 \
    --gpu-memory-utilization 0.7 \
    --load-format fastsafetensors
```

### (RECOMMENDED!!!) Running models using EUGR curated Recipes 
Supported models are listed in the recipe section of the Git repo:
- [https://github.com/eugr/spark-vllm-docker/tree/main/recipes](https://github.com/eugr/spark-vllm-docker/tree/main/recipes)

For example, you could use the recipes to launch a model like GPT-OSS_120B 
>(NOTE: You might have to compile the docker container for this to work. That could take 1 hour+)

>(IMPORTANT!!! For some models the "thinking" process could show up in the output in that case add this as arguments
> to the `./run-recipe.sh` script:  `-- --reasoning-parser qwen3`. Make sure to choose the correct parser for your model!)

```shell
### If you haven't already, source the python environment before running the recipe
source ~/myenv/bin/activate

# This will vary based on your installation. Mine is in `export VLLM_HOME=~/tmp/spark-vllm-docker`
cd $VLLM_HOME

./run-recipe.sh openai-gpt-oss-120b --solo

# -or-
./run-recipe.sh nemotron-3-super-nvfp4 --solo

# -or-
./run-recipe.sh nemotron-3-nano-nvfp4 --solo

# -or-
./run-recipe.sh qwen3-coder-next-int4-autoround --solo

# -or-
#### IMPORTANT!!!! Adding the `-- --reasoning-parser qwen3` is critical otherwise the "thinking" will show up in the
#### output along with the answer. Also, choose `openai` as the provider when using the VSCode Continue plugin.
./run-recipe.sh qwen3.6-35b-a3b-fp8 --solo -- --reasoning-parser qwen3 

# -or- (Draft model)
./run-recipe.sh qwen3.6-35b-a3b-fp8-dflash --solo
```

### Running recipes from the Nvidia community
The leaderboard page from Nvidia contains user created recipes on Spark Arena. For example:

- [https://spark-arena.com/leaderboard](https://spark-arena.com/leaderboard)

I'll use a recipe that a grabbed from the leaderboard as an example:
- [../vllm-recipes/Qwen3.6-35B-A3B-PrismaQuant-4.75bit-vllm.yaml](../vllm-recipes/Qwen3.6-35B-A3B-PrismaQuant-4.75bit-vllm.yaml)

You would run this just like the recipes in the previous section, except you would use the `.yaml` file location instead of 
the recipe name. For example:

```shell
### First we need to download the model:
hf download rdtand/Qwen3.6-35B-A3B-PrismaQuant-4.75bit-vllm

source ~/myenv/bin/activate

# This will vary based on your installation. Mine is in `export VLLM_HOME=~/tmp/spark-vllm-docker`
cd $VLLM_HOME

./run-recipe.sh ../vllm-recipes/Qwen3.6-35B-A3B-PrismaQuant-4.75bit-vllm.yaml --solo -- --reasoning-parser qwen3 
```

>(IMPORTANT!!! When accessing the model using a client, like the VSCode Continue plugin, make sure to look in the recipe for the
> `--served-model-name` property. In your continue `config.yaml`, you will use this value for the `model` property in the continue config. )

## Using the Continue Plugin as a client

### Set up the configuration file
Below is an example of a configuration file for the default model:

```yaml
name: Local Config
version: 1.0.0
schema: v1
models:
  - name: vLLM-qwen3.6-35b-a3b-fp8-thinking
    ### Use "openai" instead of "vllm" as the provider: for thinking models
    provider: openai
    model: Qwen/Qwen3.6-35B-A3B-FP8
    apiBase: http://192.168.3.210:8000/v1
    defaultCompletionOptions:
      temperature: 0.7
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

## Running personal models that aren't hosted on HuggingFace

### Using the Nvidia docker image
>(NOTE: The important point here is you have to mount a docker volume from your local OS model location to a directory inside the container using the `-v` option)

```shell
docker pull nvcr.io/nvidia/vllm:26.04-py3


docker run -it --gpus all \
  -v /home/hmuser/jupyterlab/gpt2-medium-output/final_model:/model \
  -p 8000:8000 \
  nvcr.io/nvidia/vllm:26.04-py3 \
  vllm serve /model
 ```

## Metrics
vLLM has a metrics endpoint with a huge amount of metrics data. This can be feed into something like Grafana for visualization
and monitoring.

The endpoint is: 
- http://VLLM_URL:8000/metric
- For example: http://192.168.3.210:8000/metric

An example of total output token count can be found using this property: `vllm:generation_tokens_total`

## Troubleshooting
### Troubleshooting Error messages
The following link has a list of common stack traces and error messages for vLLM
- [https://docs.vllm.ai/en/latest/usage/troubleshooting/](https://docs.vllm.ai/en/latest/usage/troubleshooting/)

