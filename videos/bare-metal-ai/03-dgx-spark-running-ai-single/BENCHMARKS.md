# Simple benchmarking for the DGX Spark

## Model Leaderboard
This is a good resource for viewing performance that other users are getting out of their DGX spark devices:

[https://spark-arena.com/leaderboard](https://spark-arena.com/leaderboard)

### The prompt
For all testing, I'm using the same prompt, using chat mode with thinking enabled (where applicable):

``` 
write Java application using the Quarkus framework. It should use the FHIR HAPI api to retrieve a patient object
```

## DGX Spark Statistics

DGX Spark uses a Grace Blackwell CPU/GPU
- **CPU** - GB10 - 20 core (ARM) - The CPU is the "Grace"
- **GPU** - GB10 - 48 Streaming Multiprocessors / 6,144 CUDA cores
- **Unified Memory** - 128 GB of LPDDR5x unified - (278 GB/s Using a 256 bit Memory Interface to the GB10 chip)
- **High Speed I/O (HSIO)** - 
- **Interconnect NVLink-C2C** - 600 GB/s - This is the interface between the GB10 chip Dielets (CPU/GPO)

### Power Usage
- **Power Off** - 1.5 watts
- **Idle** - 25-30 watts

### LLM Power Usage
- **Qwen 3.6 27B Startup** - Peaked at 150 watts with 128 GB of RAM used and 95%+ GPU usage
- **Qwen 3.6 27B Inference** - 115 watts running at 102 GB of RAM and 95%+ GPU. GPU power is 39 watts using nvidia-smi (wattage goes up some as the fan kicks in which makes sense)
- **Qwen 3.6 27B Idle** - 35-40 watts

### ComfyUI Image Power Usage
- **Qwen Image 2512 - Rendering** - Peaked at 175 watts with 40 GB of RAM used and 95%+ GPU usage (GPU using ~80-90 watts)
- **Qwen Image 2512 - Rendering temp** - Case temp is ~110 F  (78C GB-10 temp using nvidia-smi)
- **Qwen Image 2512 - Rendering time** - 5:04 mins (304.11 s) For 50 iterations (Turbo Mode off)
- **Qwen Image 2512 - Rendering time** - 22 seconds! For 50 iterations (Turbo Mode ON)

### ComfyUI Video Power Usage
- **Wen 2.2 14B - Rendering** - Peaked at 180 watts with 74 GB of RAM used and 95%+ GPU usage (GPU using ~80-90 watts)
- **Wen 2.2 14B - Rendering temp** - Case temp is ~110 F  (78C GB-10 temp using nvidia-smi)
- **Wen 2.2 14B - Rendering time** - ~15 mins for 5 seconds of 640x640 video (Turbo Mode off)
- **Wen 2.2 14B - Rendering time** - ~2 mins for 5 seconds of 640x640 video (Turbo Mode on) using ~65 GB of RAM
- **Wen 2.2 14B - Rendering time** - ~6 mins for 10 seconds of 640x640 video (Turbo Mode on) using ~75 GB of RAM
- **Wen 2.2 14B - Rendering time** - ~35-40 mins for 30 seconds of 640x640 video (Turbo Mode on) using ~100 GB of RAM

- **Wen 2.2 14B - Rendering time** - ~1:20 mins for 5 seconds of (standard def) 720x480 video (Turbo Mode on) using ~70 GB of RAM
- **Wen 2.2 14B - Rendering time** - ~3:40 mins for 10 seconds of (standard def) 720x480 video (Turbo Mode on) using ~75 GB of RAM

- **Wen 2.2 14B - Rendering time** - ~6 mins for 5 seconds of (high def) 1280x720 video (Turbo Mode on) using ~75 GB of RAM
- **Wen 2.2 14B - Rendering time** - ~20 mins for 10 seconds of (high def) 1280x720 video (Turbo Mode on) using ~85 GB of RAM

- **Wen 2.2 14B - Rendering time** - ~25 mins for 5 seconds of 1080p 1920x1080 video (Turbo Mode on) using ~85 GB of RAM

### LLM Stats for the DGX
- Qwen3.6-27b -PrismaSCOUT-Blackwell-NVFP4-BF16 draft - 20-26 t/s (55 t/s - 2 requests) (95 t/s - 4 requests)
- Qwen3.6-35b-a3b PrismQuant 4.75 draft - 60-80 t/s  (4 requests 250+ t/s!!!!)
- GPT-OSS-120b MXFP4 - 60 t/s
- Nemotron 3 Super NVFP4 - 16 t/s
- Nemotron 3 Super NVFP4 (Two GB-10s) - 25 t/s   (45 t/s - 2 requests) (70 t/s - 4 requests)
- Nemotron 3 Nano Omni NVFP4- 60 t/s
- Minimax M2.7 AWQ (Two GB-10s) - 40 t/s
- Diffusion Gemma 26B A4B-it-NVFP4 - 120 t/s  (4 requests 320+ t/s )  (NOTE: very fast thinking model, but terse results. So fast it seems like it finishes before getting the final #'s)




## (Comparison) Mac Studio Statistics
The Mac Studio is probably the natural competitor to the DGX Spark servers. Here are some statistics from the Mac:

Mac Studio
- **CPU** - M4 Max - 16 Core CPU
- **GPU** - M4 Max - 40 Core GPU 
- **Unified Memory** - 128 GB -  (546 GB/s Using a 512 bit Memory Interface to the M4 Max chip)

### Power Usage
- **Power Off** - 0.2 watts
- **Idle** - 10 watts

### LLM Power Usage
- **Qwen 3.6 27B Startup** - Peaked at 30 watts with 33 GB of RAM used 
- **Qwen 3.6 27B Inference** - 140 watts running at 33 GB of RAM and 90%+ GPU. 
- **Qwen 3.6 27B Idle** - 35-40 watts

### ComfyUI Image Power Usage

### ComfyUI Video Power Usage
- **Qwen Image 2512 - Errors Trying to convert Float8_e4m3fn to the MPS backend but it does not have support for that dtype.

### LLM Stats for the Mac Studio
- Qwen3.6-27b Q4_K_M - 23 t/s
- Qwen3.6-35b-a3b Q4_K_M - 90 t/s
- GPT-OSS-120b MXFP4 - 80 t/s
- Nemotron 3 Super Q4_K_M - 33 t/s
- Nemotron 3 Nano Omni Q4_K_M - 89 t/s
- Diffusion Gemma 26B A4B-it-Q4_K_M - 55 t/s (24/s x 2 - For 2 sessions)


### RTX 5060 on a Windows PC 
- 8GB Ram and 128bit memory bus interface GDDR7
- CUDA Cores: 3,840
- NVIDIA Blackwell (GB206) GPU

### ComfyUI Image Power Usage
- **Qwen Image 2512 - Rendering time** - 7:30 mins (441 s) For 50 iterations (Turbo Mode off)
- **Qwen Image 2512 - Rendering time** - 25 seconds! For 50 iterations (Turbo Mode ON)****

## Memory details
>(REFERENCE: The table below is from: Micron: [https://www.micron.com/products/memory/lpddr-components/lpddr5x](https://www.micron.com/products/memory/lpddr-components/lpddr5x))

| Feature | Micron LPDDR5X | Micron GDDR7 |
|---|---|---|
| Primary Use | Smartphones, thin laptops, tablets | Dedicated GPUs, AI accelerators |
| Core Priority | Battery life & heat dissipation | Raw data throughput, Bandwidth |
| Pin Speed | Up to 10.7 Gbps | 32 Gbps to 40 Gbps |
| Max Bandwidth | 100 - 200 GB/s (Typical laptop bus) | Up to 1500 GB/s (1.5 TB/s) |
| Operating Voltage | 1.05V | 1.2V |
| Signaling | Traditional NRZ (Binary) | PAM3 (Three-level signaling) |

### Calculating memory bandwidth
>(NOTE: Pin speed is in Gbps)

**DGX Spark**
```Python
bandwidth = (pin_speed * bus_width) / 8 

## For example
273 = (8.533 * 256) / 8
```

**Mac M4 Max**
```Python
## For example
547 = (8.533 * 512) / 8
```

**RTX 5060**
```Python
## For example
448 = (28 * 128) / 8
```

**RTX 5090**
```Python
## For example
1792 = (28 * 512) / 8
```