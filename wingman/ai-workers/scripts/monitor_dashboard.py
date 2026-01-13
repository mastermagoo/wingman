#!/usr/bin/env python3
"""
Real-time monitoring dashboard for LLM code generation
Shows progress, resource usage, GPU status
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime
import curses

def get_gpu_status():
    """Check GPU usage (M1 doesn't have nvidia-smi, use system stats)"""
    try:
        # Check Metal GPU usage on macOS
        result = subprocess.run(['ioreg', '-l', '-w0'],
                              capture_output=True, text=True)
        if 'gpu' in result.stdout.lower():
            return "GPU: Active"
        return "GPU: Idle"
    except:
        return "GPU: Unknown"

def get_system_stats():
    """Get CPU, RAM, and process info"""
    stats = {}

    # CPU usage
    try:
        cpu = subprocess.run(['top', '-l', '1', '-n', '0'],
                           capture_output=True, text=True)
        for line in cpu.stdout.split('\n'):
            if 'CPU usage' in line:
                stats['cpu'] = line.split(':')[1].strip()
                break
    except:
        stats['cpu'] = "N/A"

    # Memory usage
    try:
        mem = subprocess.run(['vm_stat'], capture_output=True, text=True)
        lines = mem.stdout.split('\n')
        free = int(lines[1].split()[2].rstrip('.'))
        active = int(lines[2].split()[2].rstrip('.'))
        inactive = int(lines[3].split()[2].rstrip('.'))
        wired = int(lines[6].split()[3].rstrip('.'))

        total_pages = free + active + inactive + wired
        used_pages = active + wired
        usage_pct = (used_pages / total_pages) * 100

        total_gb = (total_pages * 4096) / (1024**3)
        used_gb = (used_pages * 4096) / (1024**3)

        stats['memory'] = f"{used_gb:.1f}/{total_gb:.1f}GB ({usage_pct:.1f}%)"
    except:
        stats['memory'] = "N/A"

    # Ollama processes
    try:
        ps = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        ollama_count = sum(1 for line in ps.stdout.split('\n') if 'ollama' in line.lower())
        stats['ollama_processes'] = ollama_count
    except:
        stats['ollama_processes'] = 0

    return stats

def get_generation_progress(base_dir="/Volumes/intel-system"):
    """Track code generation progress"""
    progress = {
        'phase1_llama': {'total': 20, 'completed': 0, 'files': []},
        'production_4llama': {'completed': 0, 'files': []},
        'production_6mistral': {'completed': 0, 'files': []}
    }

    # Check Phase 1 Llama progress
    phase1_dirs = list(Path(base_dir).glob("phase1_llama8b_*/"))
    if phase1_dirs:
        latest = sorted(phase1_dirs)[-1]
        for component_dir in latest.iterdir():
            if component_dir.is_dir():
                py_files = list(component_dir.glob("*.py"))
                for f in py_files:
                    if f.stat().st_size > 100:
                        progress['phase1_llama']['completed'] += 1
                        size = f.stat().st_size / 1024
                        progress['phase1_llama']['files'].append({
                            'name': component_dir.name,
                            'size': f"{size:.1f}KB"
                        })

    # Check other deployments
    for deploy in ['production_4llama_*', 'production_6mistral_*']:
        dirs = list(Path(base_dir).glob(deploy))
        if dirs:
            latest = sorted(dirs)[-1]
            for f in latest.glob("*.py"):
                if f.stat().st_size > 100:
                    key = deploy.split('_')[1]
                    if key == '4llama':
                        progress['production_4llama']['completed'] += 1
                    else:
                        progress['production_6mistral']['completed'] += 1

    return progress

def draw_dashboard(stdscr):
    """Draw the monitoring dashboard"""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)    # Non-blocking input

    # Colors
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        header = "🚀 INTEL-SYSTEM LLM CODE GENERATION MONITOR 🚀"
        stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * width)

        # System stats
        stats = get_system_stats()
        gpu = get_gpu_status()

        row = 3
        stdscr.addstr(row, 2, "SYSTEM RESOURCES", curses.A_BOLD)
        row += 1
        stdscr.addstr(row, 4, f"CPU: {stats['cpu']}")
        row += 1
        stdscr.addstr(row, 4, f"Memory: {stats['memory']}",
                     curses.color_pair(2) if '80' in stats['memory'] else curses.color_pair(1))
        row += 1
        stdscr.addstr(row, 4, f"{gpu}",
                     curses.color_pair(3) if "Active" in gpu else curses.color_pair(1))
        row += 1
        stdscr.addstr(row, 4, f"Ollama Processes: {stats['ollama_processes']}")
        row += 2

        # Progress bars
        progress = get_generation_progress()

        stdscr.addstr(row, 2, "GENERATION PROGRESS", curses.A_BOLD)
        row += 2

        # Phase 1 progress
        phase1 = progress['phase1_llama']
        completed = phase1['completed']
        total = phase1['total']
        pct = (completed / total) * 100 if total > 0 else 0

        stdscr.addstr(row, 4, f"Phase 1 Llama 8B: {completed}/{total} components")
        row += 1

        # Progress bar
        bar_width = min(50, width - 10)
        filled = int((pct / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        color = curses.color_pair(1) if pct == 100 else curses.color_pair(2)
        stdscr.addstr(row, 4, f"[{bar}] {pct:.0f}%", color)
        row += 2

        # Recent completions
        if phase1['files']:
            stdscr.addstr(row, 4, "Recent completions:")
            row += 1
            for f in phase1['files'][-5:]:  # Show last 5
                stdscr.addstr(row, 6, f"✓ {f['name']}: {f['size']}", curses.color_pair(1))
                row += 1

        row += 1

        # GPU Warning
        if "Active" in gpu and stats['ollama_processes'] > 3:
            stdscr.addstr(row, 2, "⚠️  GPU THERMAL WARNING", curses.color_pair(3) | curses.A_BLINK)
            row += 1
            stdscr.addstr(row, 4, "M1 Max GPU is working hard but designed for this.", curses.color_pair(2))
            row += 1
            stdscr.addstr(row, 4, "Apple Silicon has excellent thermal management.", curses.color_pair(2))
            row += 2

        # Instructions
        stdscr.addstr(height-2, 2, "Press 'q' to quit | Refreshes every 2 seconds")

        stdscr.refresh()

        # Check for quit
        key = stdscr.getch()
        if key == ord('q'):
            break

        time.sleep(2)

def main():
    """Run the dashboard"""
    print("Starting monitoring dashboard...")
    print("This runs locally and won't impact LLM resources.")
    print("\nPress 'q' to quit the dashboard\n")
    time.sleep(2)

    try:
        curses.wrapper(draw_dashboard)
    except KeyboardInterrupt:
        pass

    print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()