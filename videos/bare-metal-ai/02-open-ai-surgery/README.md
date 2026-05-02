# Open AI Surgery (Patient Zero video)

Check out my YouTube Channel for more videos and content!
- [https://www.youtube.com/@HeavyMetalCloud](https://www.youtube.com/@HeavyMetalCloud)

This document walks through the process of updating Large Language Model (LLM)
weights in a model to see what the impacts will be during inference.

My goal is to simulate disease in an LLM to see if the results are similar to
cognitive symptoms found in patients.

## Dependencies and Warnings
>(WARNING!!! Running these scripts will permanently alter a model and make
> it behave in unpredictable ways.  Always make a backup of the model before beginning this
> process!)

I will be using a small model to test weight modifications. This model is:
- **Qwen2.5-coder-14b-instruct-mlx** - Using SafeTensor files for the data

>(REFERENCE: [https://huggingface.co/lmstudio-community/Qwen2.5-Coder-14B-Instruct-MLX-4bit](https://huggingface.co/lmstudio-community/Qwen2.5-Coder-14B-Instruct-MLX-4bit)

- LM Studio - You should already have LM studio installed. The Qwen model will be installed via LM Studio.
- Python - You should have python installed
- M-Chip Mac - I will assume you're running these examples on a M-chip Mac

### Download the model
Using LM Studio search for and download the following model:

- **Qwen2.5-coder-14b-instruct-mlx**

### Locate the model and make a backup copy
Next, you'll need to find the model folder. Typically, it will be located
at:

```shell
cd ~/.lmstudio/models/lmstudio-community/

## Make a backup of the model. I will call mine 'surgery"
cp Qwen2.5-Coder-14B-Instruct-MLX-4bit/Qwen2.5-Coder-14B-surgery-Instruct-MLX-4bit/

## Finally, change to the new 'surgery' version of the model for the next commands:
cd Qwen2.5-Coder-14B-surgery-Instruct-MLX-4bit/
```

### Make a backup of the SafeTensor files
There should be two SafeTensor files in this director, make a backup of each one.
The backup will act as the input for our scripts.

```shell
cp model-00001-of-00002.safetensors bkup-model-00001-of-00002.safetensors
cp model-00002-of-00002.safetensors bkup-model-00002-of-00002.safetensors
```

### Copy the scripts into the same folder as the SafeTensor files
In this Git repo are a few scripts. Two will be used and there are also
a few debug scripts, if you run into issues.  We want to copy these files over:

- `inspect-layers.py`  - This will print out all the layers in the SafeTensor file
- `update-tensors.py` - This script will update the weights in a SafeTensor file then write a new output file

```shell
cp inspect-layers.py ~/.lmstudio/models/lmstudio-community/Qwen2.5-Coder-14B-surgery-Instruct-MLX-4bit/
cp update-tensors.py ~/.lmstudio/models/lmstudio-community/Qwen2.5-Coder-14B-surgery-Instruct-MLX-4bit/
```

You should now see the `.py` scripts in the same directory as your SafeTensor files.

### View the layers in the SafeTensor files
An LLM is made up of many layers typically following this pattern:

**Embedding layer** --> **Transformer Blocks** (repeated ~50-100 times) --> **LM Head layer**

>(NOTE: The `Transformer` block is typically made of a three sub-layers: 
> 1) Multi-headed Attention
> 2) Feed Forward Network - Comprising Multilayer Perceptron networks
> 3) Normalization layer
> )

To view these layers, you can run the following scripts:

```shell
inspect-layers.py --file model-00001-of-00002.safetensors
inspect-layers.py --file model-00002-of-00002.safetensors
```

### Install a few Python dependencies with pip
```shell
pip install torch safetensors numpy
```

### Update the model weights and test with a prompt
This will be an iterative process that looks something like this:

1) Delete the safetensor file that you want to update
2) Run the `update-tensor.py` script with arguments
3) In LM Studio, Create a new chat prompt, then load the `Qwen2.5-Coder-14B-surgery-Instruct-MLX-4bit` model (NOTE: The word 'surgery' in the name is because we copied and renamed the original!)
4) Run this prompt: `Write a poem about the city of Detroit` -or- `write a Java application using quarkus that calls a FHIR server`
5) Observe if the changed models are causing issues with the output
6) Eject the model from the session in LM Studio.
7) Repeat the process for each `update-tensor.py` change

Below are the `update-tensor.py` commands I used. 

>(IMPORTANT!!! Make sure to follow the process of above for each variation of this script!!!)

>(NOTE: Since I'm using quantized models, it's important to change the `scales` and `weights` layers together.)

```shell

#### Important!!!! Weights and scales have to be updated together.


### Embedding layer
python update-tensors.py \
  --input bkup-model-00001-of-00002.safetensors \
  --output model-00001-of-00002.safetensors \
  --layers "model.embed_tokens.weight","model.embed_tokens.scales" \
  --percent 50 \
  --modifier 1.5
  
### IMPORTANT!!! Remember to go through all the steps in the workflow after running each one of these!!!!

### Attention query, first layer
python update-tensors.py \
  --input bkup-model-00001-of-00002.safetensors \
  --output model-00001-of-00002.safetensors \
  --layers "model.layers.0.self_attn.q_proj.weight","model.layers.0.self_attn.q_proj.scales" \
  --percent 70 \
  --modifier 3.5

### first file MLP
python update-tensors.py \
  --input bkup-model-00001-of-00002.safetensors \
  --output model-00001-of-00002.safetensors \
  --layers "model.layers.3.mlp.up_proj.weight","model.layers.3.mlp.up_proj.scales" \
  --percent 70 \
  --modifier 2.5

### 2nd file MLP
python update-tensors.py \
  --input bkup-model-00002-of-00002.safetensors \
  --output model-00002-of-00002.safetensors \
  --layers "model.layers.33.mlp.up_proj.weight","model.layers.33.mlp.up_proj.scales" \
  --percent 70 \
  --modifier 2.5

#### 2nd file, 2 layers updated at once
#### This first run doesn't change the weights enough to notice  difference
python update-tensors.py \
  --input bkup-model-00002-of-00002.safetensors \
  --output model-00002-of-00002.safetensors \
  --layers model.layers.33.mlp.up_proj.weight,model.layers.33.mlp.up_proj.scales,model.layers.40.mlp.up_proj.weight,model.layers.40.mlp.up_proj.scales \
  --percent 70 \
  --modifier 2

#### 2nd file, 2 layers updated at once, part 2
#### Increasing the modifier (amount the weight is modified) causes changes to occur
python update-tensors.py \
  --input bkup-model-00002-of-00002.safetensors \
  --output model-00002-of-00002.safetensors \
  --layers model.layers.33.mlp.up_proj.weight,model.layers.33.mlp.up_proj.scales,model.layers.40.mlp.up_proj.weight,model.layers.40.mlp.up_proj.scales \
  --percent 70 \
  --modifier 2.1

#### 2nd file, update the final LM Head layer
### careful with this one it’s the last layer. Minor changes can break things
python update-tensors.py \
  --input bkup-model-00002-of-00002.safetensors \
  --output model-00002-of-00002.safetensors \
  --layers lm_head.weight,lm_head.scales \
  --percent 25 \
  --modifier 1.5


```

### (OPTIONAL) Code Generation of the scripts
To create the `inspect-layers.py` and  `update-tensors.py` scripts, I used a more sophisticated LLM model
called, `Qwen3.5 35B A3b`
- [https://huggingface.co/Qwen/Qwen3.5-35B-A3B](https://huggingface.co/Qwen/Qwen3.5-35B-A3B)

Here are the prompts I used to initially created the code. If I ran into errors or issues, I would then paste the 
error into the same session then update the script with the changes.

>(NOTE: Due to the non-deterministic nature of LLM's, you will get different code generated than I did.)

**Prompt for `inspect-layers.py`**:
``` 
Using python, create a script that will print out all the layers in a safe tensor file. 
This script should externalize the arguments for the safetensor file
```

**Prompt for `update-tensors.py`**:
```
Using python, create a script that will randomly modify weights in a safetensor file. 
This script should externalizable parameters for the percentage of the total weights 
you want to modify and also a property to adjust how much the weight is changed. 
(let's use multiplication for this, with a default value of 2 times multiplier). 
Also this script should be able to modify quantized models where the 
weights are integer values and not just floating point
```