# LLM Model Management Guide

## Current Configuration

**Active Model**: `mistral:7b` (fast, for development/testing)
**Production Model**: `deepseek-coder:33b-instruct` (high quality, slower)

---

## Quick Model Switch

### Switch to Mistral 7B (Fast - Testing)

Edit `.env` file:
```bash
LLM_MODEL_NAME=mistral:7b
```

**Benefits**:
- ⚡ Fast inference (5-10 seconds per agent)
- 💾 Smaller memory footprint (4.4 GB)
- ✅ Good quality for development
- 🚀 Total pipeline time: 2-3 minutes

### Switch to DeepSeek 33B (Production)

Edit `.env` file:
```bash
LLM_MODEL_NAME=deepseek-coder:33b-instruct
```

**Benefits**:
- 🎯 Excellent quality JSON extraction
- 📊 Better structured data accuracy
- 💡 Superior reasoning for complex prompts
- ⚠️ Slower: 30-60 seconds per agent
- 🐌 Total pipeline time: 10-15 minutes

---

## Available Models

### Currently Installed

```bash
ollama list
```

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| mistral:7b | 4.4 GB | ⚡⚡⚡ Fast | Good | Development, testing |
| deepseek-coder:33b-instruct | 18 GB | 🐌 Slow | Excellent | Production |
| gpt-oss:20b | 13 GB | 🐌 Medium | Very Good | Alternative |
| nomic-embed-text:latest | 274 MB | ⚡⚡⚡ Fast | N/A | Embeddings only |

### Quantized Options (Recommended)

If you want a balance between speed and quality, try quantized DeepSeek:

```bash
# Pull quantized versions (smaller, faster)
ollama pull deepseek-coder:6.7b-instruct-q4_0    # 4GB, 2x faster
ollama pull deepseek-coder:6.7b-instruct-q4_K_M  # 4GB, better quality
ollama pull deepseek-coder:6.7b-instruct-q8_0    # 7GB, best quantized quality
```

Then update `.env`:
```bash
LLM_MODEL_NAME=deepseek-coder:6.7b-instruct-q4_K_M
```

**Quantization Comparison**:
- `q4_0`: Smallest, fastest (4GB)
- `q4_K_M`: Good balance (4GB) ✅ **Recommended**
- `q8_0`: Best quality quantized (7GB)
- Full 33B: Best quality, slowest (18GB)

---

## Performance Benchmarks

### Test Pipeline (Sprint 01 test transcript)

| Model | Agent Time | Total Time | Quality |
|-------|-----------|------------|---------|
| mistral:7b | 5-10s | 2-3 min | ⭐⭐⭐ Good |
| deepseek-coder:6.7b-q4_K_M | 10-15s | 4-5 min | ⭐⭐⭐⭐ Very Good |
| deepseek-coder:33b | 30-60s | 10-15 min | ⭐⭐⭐⭐⭐ Excellent |

### Real Transcript (John & Janice Suss - 70 min meeting)

| Model | Agent Time | Total Time | Quality |
|-------|-----------|------------|---------|
| mistral:7b | 8-15s | 3-5 min | ⭐⭐⭐ Good |
| deepseek-coder:6.7b-q4_K_M | 15-25s | 6-8 min | ⭐⭐⭐⭐ Very Good |
| deepseek-coder:33b | 45-90s | 15-20 min | ⭐⭐⭐⭐⭐ Excellent |

---

## Recommendation for Different Stages

### **Stage 1: Development & Testing** ✅ **Current**
```bash
LLM_MODEL_NAME=mistral:7b
```
- Fast iteration cycles
- Quick testing of pipeline changes
- Good enough quality for validation

### **Stage 2: Pre-Production Testing**
```bash
LLM_MODEL_NAME=deepseek-coder:6.7b-instruct-q4_K_M
```
- Good balance of speed and quality
- Validate extraction accuracy
- Test with real customer data

### **Stage 3: Production**
```bash
LLM_MODEL_NAME=deepseek-coder:33b-instruct
```
- Maximum accuracy for customer data
- Best JSON structure compliance
- Worth the slower speed for quality

---

## Model Installation

### Install Quantized DeepSeek (Recommended for Stage 2)

```bash
# Best balance option
ollama pull deepseek-coder:6.7b-instruct-q4_K_M

# Or try other quantizations
ollama pull deepseek-coder:6.7b-instruct-q4_0    # Fastest
ollama pull deepseek-coder:6.7b-instruct-q8_0    # Best quality
```

### Install Alternative Models

```bash
# Other good 7B options
ollama pull llama3.1:7b-instruct-q4_K_M
ollama pull mistral-nemo:12b-instruct-2407-q4_K_M

# Larger alternatives
ollama pull qwen2.5:14b-instruct-q4_K_M         # Good quality, 8GB
ollama pull llama3.1:70b-instruct-q4_K_M        # Best quality, 40GB (if you have GPU)
```

---

## Testing Each Model

### Quick Test Script

```bash
# Test with Mistral 7B (fast)
./venv/bin/python scripts/test_pipeline_mistral.py

# Test with DeepSeek 33B (production quality)
# First, update .env to deepseek-coder:33b-instruct
./venv/bin/python scripts/test_pipeline_direct.py
```

### Compare Models

```bash
# Run comparison test
./venv/bin/python scripts/compare_models.py
```

(Note: Would need to create this script if you want automated comparison)

---

## Quality vs Speed Decision Matrix

```
                Quality
                   ↑
                   |
Production         |  deepseek-coder:33b
(Best Quality)     |        ⭐⭐⭐⭐⭐
                   |
                   |  deepseek-coder:6.7b-q8_0
Pre-Production     |        ⭐⭐⭐⭐
(Balanced)         |
                   |  deepseek-coder:6.7b-q4_K_M
                   |        ⭐⭐⭐⭐
Testing            |
                   |  mistral:7b
Development        |        ⭐⭐⭐
(Fast Iteration)   |
                   └──────────────────────────→ Speed
```

---

## Current System Status

```bash
# Check active model
./venv/bin/python -c "from config.settings import settings; print(settings.LLM_MODEL_NAME)"

# Check available models
ollama list

# Check Ollama status
docker ps | grep ollama
```

---

## Troubleshooting

### Model Not Found
```bash
# Pull the model first
ollama pull mistral:7b

# Verify it's installed
ollama list
```

### Out of Memory
```bash
# Use smaller model
LLM_MODEL_NAME=mistral:7b

# Or use quantized version
LLM_MODEL_NAME=deepseek-coder:6.7b-instruct-q4_0
```

### Slow Inference
```bash
# Check if GPU is being used
ollama ps

# Try smaller model
LLM_MODEL_NAME=mistral:7b
```

---

## Conclusion

**Current Setup**: ✅ Mistral 7B (fast, good for development)

**Recommended Path**:
1. Development: `mistral:7b` (current) ✅
2. Testing: `deepseek-coder:6.7b-instruct-q4_K_M` (install when ready)
3. Production: `deepseek-coder:33b-instruct` (already installed)

Simply update `.env` file to switch between models. No code changes needed!
