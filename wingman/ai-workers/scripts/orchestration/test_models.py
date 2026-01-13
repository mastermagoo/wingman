#!/usr/bin/env python3
"""
Test both models directly without AutoGen
"""

import subprocess
import time
import json

def test_model(model_name, prompt):
    """Test a model with a prompt"""
    print(f"\n🧠 Testing {model_name}...")
    print(f"Prompt: {prompt[:100]}...")

    start = time.time()

    cmd = f'ollama run {model_name} "{prompt}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

    elapsed = time.time() - start

    print(f"✅ Response received in {elapsed:.1f} seconds")
    print(f"Output length: {len(result.stdout)} characters")
    print("-" * 40)
    print(result.stdout[:500])
    print("-" * 40)

    return result.stdout, elapsed

# Test both models
print("🔬 MODEL COMPARISON TEST")
print("=" * 50)

# Simple task for 7B
prompt_7b = "Write a Python function to connect to Redis and store a key-value pair"
output_7b, time_7b = test_model("mistral:7b", prompt_7b)

# Complex task for 13B
prompt_13b = """Create a Python class for a RAG pipeline that:
1. Uses ChromaDB for vector storage
2. Has methods for add_document and search
3. Includes error handling
Only output code, no explanations."""

output_13b, time_13b = test_model("codellama:13b", prompt_13b)

print("\n📊 RESULTS:")
print(f"Mistral 7B: {time_7b:.1f}s for {len(output_7b)} chars")
print(f"CodeLlama 13B: {time_13b:.1f}s for {len(output_13b)} chars")
print(f"\nSpeed ratio: {time_13b/time_7b:.1f}x slower")
print(f"Output ratio: {len(output_13b)/len(output_7b):.1f}x more detailed")

# Save outputs
with open("/Volumes/intel-system/model_outputs.txt", "w") as f:
    f.write("MISTRAL 7B OUTPUT:\n")
    f.write("=" * 50 + "\n")
    f.write(output_7b)
    f.write("\n\nCODELLAMA 13B OUTPUT:\n")
    f.write("=" * 50 + "\n")
    f.write(output_13b)

print("\n✅ Outputs saved to model_outputs.txt")
print("\n🎯 RECOMMENDATION:")
if time_13b < 30:
    print("13B is fast enough! Use for all complex tasks.")
else:
    print("13B is slower but worth it for complex tasks.")
    print("Use hybrid: 13B for architecture, 7B for simple tasks.")