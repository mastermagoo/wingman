#!/usr/bin/env python3
"""
Compare ALL Major LLMs for Python Code Generation
Fair comparison with identical prompts and scoring
"""

import subprocess
import time
import json
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test ALL our best models
MODELS_TO_TEST = [
    "yi-coder:9b",          # 5.0GB - Yi specialized for coding
    "llama3.1:8b",          # 4.9GB - Meta's latest
    "mistral:7b",           # 4.4GB - Strong general purpose
    "starcoder2:7b",        # 4.0GB - Specialized for code
    "deepseek-coder:6.7b",  # 3.8GB - DeepSeek's code model
]

# Same test prompt for all models
TEST_PROMPT = """Create a production-ready Python REST API service with the following:

1. FastAPI framework
2. User authentication with JWT tokens
3. SQLAlchemy ORM with PostgreSQL
4. Redis caching
5. Rate limiting middleware
6. Comprehensive error handling
7. Logging with structured logs
8. Input validation with Pydantic
9. CORS configuration
10. Health check endpoint

Include ALL necessary imports, configuration, and make it completely runnable.
Write the complete code immediately without explanations."""

def analyze_code_quality(code_content):
    """Score the generated code on various metrics"""
    scores = {}

    # Check for imports
    imports = len(re.findall(r'^import |^from .+ import', code_content, re.MULTILINE))
    scores['imports'] = min(imports * 5, 30)  # Max 30 points

    # Check for error handling
    try_except = len(re.findall(r'\btry:', code_content))
    scores['error_handling'] = min(try_except * 10, 20)  # Max 20 points

    # Check for FastAPI endpoints
    endpoints = len(re.findall(r'@app\.(get|post|put|delete|patch)', code_content))
    scores['endpoints'] = min(endpoints * 5, 20)  # Max 20 points

    # Check for authentication
    auth_keywords = ['JWT', 'jwt', 'token', 'authenticate', 'OAuth2']
    auth_score = sum(2 for keyword in auth_keywords if keyword in code_content)
    scores['authentication'] = min(auth_score, 10)  # Max 10 points

    # Check for database/ORM
    db_keywords = ['SQLAlchemy', 'Base', 'Session', 'Column', 'Integer', 'String']
    db_score = sum(2 for keyword in db_keywords if keyword in code_content)
    scores['database'] = min(db_score, 10)  # Max 10 points

    # Check for structure/organization
    classes = len(re.findall(r'^class \w+', code_content, re.MULTILINE))
    functions = len(re.findall(r'^def \w+', code_content, re.MULTILINE))
    scores['structure'] = min((classes * 3 + functions * 2), 10)  # Max 10 points

    # Total score
    scores['total'] = sum(v for k, v in scores.items() if k != 'total')

    return scores

def test_model(model_name, output_dir):
    """Test a single model and return results"""
    print(f"\n🤖 Testing {model_name}...")

    output_file = output_dir / f"{model_name.replace(':', '_')}.py"
    start_time = time.time()

    # Run the model
    cmd = f'ollama run {model_name} "{TEST_PROMPT}" > {output_file} 2>/dev/null'
    result = subprocess.run(cmd, shell=True, timeout=120)

    duration = time.time() - start_time

    # Analyze results
    if output_file.exists():
        with open(output_file, 'r', errors='ignore') as f:
            content = f.read()

        size = len(content)
        lines = content.count('\n')

        # Clean up the content (remove markdown if present)
        if '```python' in content:
            # Extract code from markdown
            code_blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
            if code_blocks:
                content = '\n'.join(code_blocks)

        # Check syntax validity
        syntax_valid = False
        try:
            compile(content, output_file, 'exec')
            syntax_valid = True
        except SyntaxError as e:
            pass

        # Score the code
        scores = analyze_code_quality(content)

        # Get first few lines for preview
        preview_lines = content.split('\n')[:5]

        return {
            'model': model_name,
            'success': True,
            'duration': duration,
            'size': size,
            'lines': lines,
            'syntax_valid': syntax_valid,
            'scores': scores,
            'preview': preview_lines
        }
    else:
        return {
            'model': model_name,
            'success': False,
            'duration': duration,
            'size': 0,
            'lines': 0,
            'syntax_valid': False,
            'scores': {'total': 0},
            'preview': []
        }

def main():
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"/Volumes/intel-system/llm_comparison_{timestamp}")
    output_dir.mkdir(exist_ok=True)

    print("="*80)
    print(" LLM PYTHON CODE GENERATION COMPARISON ".center(80))
    print("="*80)
    print(f"\n📁 Output: {output_dir}")
    print(f"🤖 Models: {len(MODELS_TO_TEST)} models being tested")
    print(f"⏰ Started: {datetime.now()}\n")

    # Test all models
    results = []
    for model in MODELS_TO_TEST:
        try:
            result = test_model(model, output_dir)
            results.append(result)

            print(f"   ✅ Completed in {result['duration']:.1f}s")
            print(f"   📊 Score: {result['scores']['total']}/100")
            print(f"   📝 Size: {result['size']:,} bytes, {result['lines']} lines")
            print(f"   🔧 Valid Python: {'✅' if result['syntax_valid'] else '❌'}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                'model': model,
                'success': False,
                'scores': {'total': 0}
            })

    # Sort by score
    results.sort(key=lambda x: x['scores']['total'], reverse=True)

    # Display comparison
    print("\n" + "="*80)
    print(" FINAL RANKINGS ".center(80))
    print("="*80 + "\n")

    print("LEADERBOARD:")
    print("-"*80)
    print(f"{'Rank':<5} {'Model':<25} {'Score':<10} {'Time':<10} {'Size':<12} {'Valid':<8}")
    print("-"*80)

    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"{i:<5} {result['model']:<25} "
                  f"{result['scores']['total']:>3}/100    "
                  f"{result['duration']:>6.1f}s    "
                  f"{result['size']:>8,}B    "
                  f"{'✅' if result['syntax_valid'] else '❌'}")
        else:
            print(f"{i:<5} {result['model']:<25} FAILED")

    # Detailed scoring breakdown for top 3
    print("\n" + "="*80)
    print(" TOP 3 DETAILED SCORES ".center(80))
    print("="*80 + "\n")

    for i, result in enumerate(results[:3], 1):
        if result['success']:
            print(f"#{i} {result['model']}")
            print(f"   Total Score: {result['scores']['total']}/100")
            print(f"   Breakdown:")
            for metric, score in result['scores'].items():
                if metric != 'total':
                    print(f"      {metric:20}: {score:>3}")
            print(f"   Preview:")
            for line in result['preview'][:3]:
                if line.strip():
                    print(f"      {line[:70]}")
            print()

    # Save results
    results_file = output_dir / "comparison_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"📊 Full results saved to: {results_file}")

    # Winner
    winner = results[0] if results else None
    if winner and winner['success']:
        print(f"\n🏆 WINNER: {winner['model']} with score {winner['scores']['total']}/100")
        print(f"   Best at: {', '.join(k for k, v in winner['scores'].items() if k != 'total' and v > 5)}")

    return results

if __name__ == "__main__":
    print("🔍 Verifying all models are available...\n")

    for model in MODELS_TO_TEST:
        result = subprocess.run(f"ollama list | grep '{model}'",
                              shell=True, capture_output=True, text=True)
        if model in result.stdout:
            # Get size
            size = result.stdout.split()[2]
            print(f"✅ {model:<20} ({size})")
        else:
            print(f"❌ {model:<20} NOT AVAILABLE")

    print("\nStarting comparison test...\n")
    results = main()