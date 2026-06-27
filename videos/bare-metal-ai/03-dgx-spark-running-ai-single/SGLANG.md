# Installing SGLANG on a Spark
>(NOTE: SGLANG will run via a docker container. See below)

## Installation and operation
>(REFERENCE: 
> - [https://build.nvidia.com/spark/sglang/instructions](https://build.nvidia.com/spark/sglang/instructions)
> - [https://www.lmsys.org/blog/2025-11-03-gpt-oss-on-nvidia-dgx-spark/](https://www.lmsys.org/blog/2025-11-03-gpt-oss-on-nvidia-dgx-spark/)
> )

>(NOTE: Ideally, you should point your volume mount to your local huggingface cache directory. This is especially useful if using other
> serving platforms like vLLM, for model reuse. This is usually located at: `~/.cache/huggingface`)

### Pull the Docker image
```shell
# Pull the SGLang container
docker pull nvcr.io/nvidia/sglang:26.02-py3

# Verify the image was downloaded
docker images | grep sglang
```


## Run models using Docker
For all the models, you will first have to start up the docker container:

```shell
docker run --gpus all -it --rm \
  --memory="80G" \
  --shm-size=30G \
  -p 30000:30000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
   --ipc=host --ulimit memlock=-1 --ulimit stack=67108864  \
  nvcr.io/nvidia/sglang:26.02-py3 \
  bash
  
docker run --gpus all -it --rm \
  -p 30000:30000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
   --ipc=host --ulimit memlock=-1 --ulimit stack=67108864  \
  nvcr.io/nvidia/sglang:26.02-py3 \
  bash
```

### Deepseek
```shell
python3 -m sglang.launch_server \
  --model-path deepseek-ai/DeepSeek-V2-Lite \
  --host 0.0.0.0 \
  --port 30000 \
  --trust-remote-code \
  --tp 1 \
  --disable-cuda-graph \
  --attention-backend flashinfer \
  --mem-fraction-static 0.75 &
```

### Nemotron 3 Nano
```shell
python3 -m sglang.launch_server \
    --model nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 \
    --served-model-name nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 \
    --host 0.0.0.0 --port 30000 \
    --reasoning-parser nano_v3 \
    --tp 1 \
    --ep 1 \
    --disable-cuda-graph \
    --mem-fraction-static 0.8 &
```

### Nemotron 3 Super
```shell

python3 -m sglang.launch_server \
    --model nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 \
    --served-model-name nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 \
    --host 0.0.0.0 --port 30000 \
    --trust-remote-code \
    --tp 1 \
    --ep 1 \
    --tool-call-parser qwen3_coder \
    --reasoning-parser nano_v3 \
    --quantization modelopt_fp4 \
    --reasoning-parser nano_v3 \
    --mem-fraction-static 0.8 &
```
pip install --upgrade sglang --extra-index-url https://flashinfer.ai
pip install --upgrade transformers

python3 -m sglang.launch_server \
    --model Qwen/Qwen3.6-35B-A3B-FP8 \
    --served-model-name Qwen/Qwen3.6-35B-A3B-FP8 \
    --host 0.0.0.0 --port 30000 \
    --reasoning-parser qwen3 \
    --attention-backend triton \
    --context-length 131072 \
    --tp-size 1 \
    --tool-call-parser qwen3_coder \
    --mem-fraction-static 0.7

python3 -m sglang.launch_server \
    --model openai/gpt-oss-120b \
    --served-model-name openai/gpt-oss-120b \
    --host 0.0.0.0 --port 30000 \
    --reasoning-parser gpt-oss \
    --tp 1 --mem-fraction-static 0.8 &

