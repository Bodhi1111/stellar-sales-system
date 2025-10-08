# LLM Model Quick Reference Card

## 🚀 Quick Model Switch

Edit `.env` and change one line:

```bash
# Current: Development (Fast)
LLM_MODEL_NAME=mistral:7b

# Next: Pre-Production (Balanced) ← RECOMMENDED NEXT STEP
LLM_MODEL_NAME=deepseek-coder:6.7b-instruct-q4_K_M

# Later: Production (Best Quality)
LLM_MODEL_NAME=deepseek-coder:33b-instruct
```

Then restart your test!

---

## 📊 Model Comparison (At a Glance)

| Metric | Mistral 7B | DeepSeek 6.7B (Q) | DeepSeek 33B |
|--------|------------|-------------------|--------------|
| **Size** | 4.4 GB | 4.1 GB | 18 GB |
| **Speed** | ⚡⚡⚡ Fast | ⚡⚡ Medium | 🐌 Slow |
| **Quality** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐⭐⭐ Excellent |
| **Pipeline Time** | 1-3 min | 4-6 min | 10-15 min |
| **Use Case** | Development | Pre-Production | Production |
| **Status** | ✅ Current | ✅ Installed | ✅ Ready |

---

## ✅ All Models Installed

```
mistral:7b                             4.4 GB  ✅
deepseek-coder:6.7b-instruct-q4_K_M    4.1 GB  ✅
deepseek-coder:33b-instruct            18 GB   ✅
```

**Total disk space**: 26.5 GB

---

## 🎯 Recommended Path

1. **Now**: Development with `mistral:7b` ✅
2. **Next Week**: Testing with `deepseek-coder:6.7b-instruct-q4_K_M` 🎯
3. **Production**: Deploy with `deepseek-coder:33b-instruct` 🚀

---

## 📝 Quick Test Commands

```bash
# Verify current model
./venv/bin/python -c "from config.settings import settings; print(settings.LLM_MODEL_NAME)"

# Quick test (2-3 minutes)
./venv/bin/python scripts/test_pipeline_quick.py

# Full pipeline test
./venv/bin/python scripts/test_pipeline_mistral.py

# Check installed models
ollama list
```

---

**Full docs**: [MODEL_TRANSITION_PLAN.md](docs/MODEL_TRANSITION_PLAN.md)
