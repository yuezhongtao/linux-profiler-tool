#!/usr/bin/env python3
"""
Example workflow demonstrating process search and profiling features.

This script shows how to:
1. Search for processes by keyword
2. Select a target process
3. Profile the process using perf
4. Generate flame graph data
"""

import json
import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from linux_profiler.collectors import ProcessCollector, PerfCollector


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def search_processes_example(keyword: str = "python"):
    """Example: Search for processes by keyword."""
    print_section(f"1. Searching for processes with keyword: '{keyword}'")
    
    collector = ProcessCollector()
    result = collector.search_processes(keyword, case_sensitive=False)
    
    print(f"Search Status: {result['success']}")
    print(f"Matched Processes: {result['matched_count']}")
    
    if result['success'] and result['processes']:
        print(f"\nTop 5 Matched Processes (by CPU usage):\n")
        for i, proc in enumerate(result['processes'][:5], 1):
            print(f"{i}. PID: {proc['pid']:6d} | "
                  f"Name: {proc['name']:20s} | "
                  f"CPU: {proc['cpu_percent']:5.1f}% | "
                  f"Memory: {proc['memory_percent']:5.1f}%")
            if proc['cmdline']:
                print(f"   Command: {proc['cmdline'][:80]}")
        
        return result['processes']
    else:
        print("No processes found or error occurred.")
        if 'error' in result:
            print(f"Error: {result['error']}")
        return []


def profile_process_example(pid: int, duration: int = 10):
    """Example: Profile a specific process."""
    print_section(f"2. Profiling process PID {pid} for {duration} seconds")
    
    print(f"⏱️  Collecting performance data (this will take {duration} seconds)...")
    print("Note: This requires 'perf' tool to be installed on your system.\n")
    
    collector = PerfCollector()
    result = collector.collect_process_profile(
        pid=pid,
        duration=duration,
        frequency=99,
        event="cpu-clock"
    )
    
    if not result['success']:
        print(f"❌ Profiling failed: {result['error']}")
        if 'help' in result:
            print(f"💡 Help: {result['help']}")
        return None
    
    print("✅ Profiling completed successfully!\n")
    
    # Display statistics
    stats = result.get('statistics', {})
    print("📊 Performance Statistics:")
    print(f"   Total samples: {stats.get('total_samples', 0)}")
    
    top_funcs = stats.get('top_functions', [])
    if top_funcs:
        print(f"\n   Top {min(10, len(top_funcs))} CPU-consuming functions:")
        for i, func in enumerate(top_funcs[:10], 1):
            print(f"   {i:2d}. {func['overhead_percent']:5.1f}% - "
                  f"{func['function'][:60]}")
    
    # Flame graph data
    flame_data = result.get('flame_graph_data', [])
    print(f"\n🔥 Flame Graph Data:")
    print(f"   Stack samples collected: {len(flame_data)}")
    
    if flame_data:
        print(f"\n   Sample stack trace (first sample):")
        first_sample = flame_data[0]
        print(f"   Command: {first_sample.get('command', 'unknown')}")
        print(f"   Stack depth: {len(first_sample.get('stack', []))}")
        for frame in first_sample.get('stack', [])[:5]:
            print(f"      ↓ {frame}")
        if len(first_sample.get('stack', [])) > 5:
            print(f"      ... ({len(first_sample['stack']) - 5} more frames)")
    
    return result


def save_flame_graph_data(flame_data: list, output_file: str = "flame_data.txt"):
    """Save flame graph data to file for visualization."""
    print_section("3. Saving Flame Graph Data")
    
    output_path = Path(output_file)
    lines = []
    
    for sample in flame_data:
        if sample.get('stack'):
            command = sample.get('command', 'unknown')
            stack_trace = ';'.join(sample['stack'])
            lines.append(f"{command};{stack_trace} 1")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Flame graph data saved to: {output_path.absolute()}")
    print(f"   Total stack traces: {len(lines)}")
    print(f"\n💡 Generate flame graph using:")
    print(f"   cat {output_file} | flamegraph.pl > flame.svg")
    print(f"   # or upload to https://www.speedscope.app/")
    
    return output_path


def interactive_workflow():
    """Interactive workflow for process profiling."""
    print_section("Linux Profiler - Process Search and Profiling Demo")
    
    # Step 1: Search for processes
    keyword = input("Enter keyword to search for processes (default: python): ").strip()
    if not keyword:
        keyword = "python"
    
    processes = search_processes_example(keyword)
    
    if not processes:
        print("\n❌ No processes found. Exiting.")
        return
    
    # Step 2: Select a process
    print(f"\n" + "─"*60)
    pid_input = input("Enter PID to profile (or press Enter to skip profiling): ").strip()
    
    if not pid_input:
        print("Profiling skipped.")
        return
    
    try:
        pid = int(pid_input)
    except ValueError:
        print(f"❌ Invalid PID: {pid_input}")
        return
    
    # Validate PID is in the list
    if not any(p['pid'] == pid for p in processes):
        print(f"⚠️  Warning: PID {pid} was not in the search results.")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    # Step 3: Choose duration
    duration_input = input("Enter profiling duration in seconds (default: 10): ").strip()
    duration = 10
    if duration_input:
        try:
            duration = int(duration_input)
            if not (1 <= duration <= 300):
                print("Duration must be between 1 and 300 seconds. Using default: 10")
                duration = 10
        except ValueError:
            print("Invalid duration. Using default: 10")
    
    # Step 4: Profile the process
    result = profile_process_example(pid, duration)
    
    if result and result['success']:
        # Step 5: Save flame graph data
        flame_data = result.get('flame_graph_data', [])
        if flame_data:
            save_choice = input("\nSave flame graph data? (y/n): ").strip().lower()
            if save_choice == 'y':
                output_file = input("Output filename (default: flame_data.txt): ").strip()
                if not output_file:
                    output_file = "flame_data.txt"
                save_flame_graph_data(flame_data, output_file)


def automated_example():
    """Automated example with preset values."""
    print_section("Automated Example: Search and Profile")
    
    # Search for python processes
    processes = search_processes_example("python")
    
    if processes:
        # Profile the first process for 5 seconds
        pid = processes[0]['pid']
        result = profile_process_example(pid, duration=5)
        
        if result and result['success']:
            # Save flame graph data
            flame_data = result.get('flame_graph_data', [])
            if flame_data:
                save_flame_graph_data(flame_data, "example_flame_data.txt")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        automated_example()
    else:
        try:
            interactive_workflow()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Exiting...")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
