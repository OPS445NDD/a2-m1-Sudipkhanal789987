#!/usr/bin/env python3

'''
OPS445 Assignment 2 - Fall 2025
Program: assignment2.py
Author: Sudip Khanal

The python code in this file is original work written by
Sudip Khanal. No code in this file is copied from any other source
except those provided by the course instructor, including any person,
textbook, or on-line resource. I have not shared this python script
with anyone or anything except for submission for grading.
I understand that the Academic Honesty Policy will be enforced and
violators will be reported and appropriate action will be taken.

Description: Displays total system memory usage or the resident memory
usage of every process associated with a specified running program.
Memory usage is presented with a configurable bar graph and can be
shown in either KiB or human-readable units.

Date: July 17, 2026
'''

import argparse
import os
import sys


def parse_command_args() -> object:
    """Parse and return command-line options and the optional program name."""
    parser = argparse.ArgumentParser(
        description=(
            "Memory Visualiser -- See Memory Usage Report with bar charts"
        ),
        epilog="Copyright 2023"
    )
    parser.add_argument(
        "-H",
        "--human-readable",
        action="store_true",
        help="Prints sizes in human readable format"
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=20,
        help="Specify the length of the graph. Default is 20."
    )
    parser.add_argument(
        "program",
        type=str,
        nargs="?",
        help=(
            "if a program is specified, show memory use of all associated "
            "processes. Show only total use if not."
        )
    )
    return parser.parse_args()


def percent_to_graph(percent: float, length: int = 20) -> str:
    """Convert a decimal percentage into a graph of hashes and spaces."""
    # Keep the graph inside its requested boundaries if input is unexpected.
    percent = max(0.0, min(percent, 1.0))
    graph_length = max(0, length)
    hash_count = round(percent * graph_length)
    return "#" * hash_count + " " * (graph_length - hash_count)


def get_sys_mem() -> int:
    """Return total system memory from /proc/meminfo in KiB."""
    with open("/proc/meminfo", "r") as meminfo:
        for line in meminfo:
            if line.startswith("MemTotal:"):
                return int(line.split()[1])
    return 0


def get_avail_mem() -> int:
    """Return currently available system memory from /proc/meminfo in KiB."""
    mem_free = 0
    swap_free = 0

    with open("/proc/meminfo", "r") as meminfo:
        for line in meminfo:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
            if line.startswith("MemFree:"):
                mem_free = int(line.split()[1])
            elif line.startswith("SwapFree:"):
                swap_free = int(line.split()[1])

    # Some WSL systems do not provide MemAvailable.
    return mem_free + swap_free


def pids_of_prog(app_name: str) -> list:
    """Return a list of process IDs associated with a running program."""
    # pidof returns process IDs separated by whitespace on one output line.
    pid_output = os.popen(f"pidof {app_name}").read().strip()
    if not pid_output:
        return []
    return pid_output.split()


def rss_mem_of_pid(proc_id: str) -> int:
    """Return the total resident memory used by one process in KiB."""
    rss_total = 0
    smaps_path = f"/proc/{proc_id}/smaps"

    try:
        with open(smaps_path, "r") as smaps_file:
            for line in smaps_file:
                if line.startswith("Rss:"):
                    rss_total += int(line.split()[1])
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        # A process can end or become inaccessible while the report is made.
        return 0

    return rss_total


def bytes_to_human_r(kibibytes: int, decimal_places: int = 2) -> str:
    """Convert a KiB memory amount to an appropriate binary unit."""
    suffixes = ["KiB", "MiB", "GiB", "TiB", "PiB"]
    suffix_index = 0
    result = float(kibibytes)

    # Divide by 1024 until the amount fits the most useful available unit.
    while result >= 1024 and suffix_index < len(suffixes) - 1:
        result /= 1024
        suffix_index += 1

    return f"{result:.{decimal_places}f} {suffixes[suffix_index]}"


def display_memory_line(
        label: str,
        used_memory: int,
        total_memory: int,
        graph_length: int,
        human_readable: bool) -> None:
    """Print one consistently formatted memory usage report line."""
    memory_percent = used_memory / total_memory if total_memory else 0
    graph = percent_to_graph(memory_percent, graph_length)

    if human_readable:
        used_output = bytes_to_human_r(used_memory)
        total_output = bytes_to_human_r(total_memory)
    else:
        used_output = str(used_memory)
        total_output = str(total_memory)

    print(
        f"{label:<15}[{graph}| {memory_percent:.0%}] "
        f"{used_output}/{total_output}"
    )


def main() -> None:
    """Run the memory visualiser using the supplied command-line arguments."""
    args = parse_command_args()

    if args.length < 1:
        print("Graph length must be greater than zero.", file=sys.stderr)
        sys.exit(1)

    total_memory = get_sys_mem()

    if not args.program:
        used_memory = total_memory - get_avail_mem()
        display_memory_line(
            "Memory",
            used_memory,
            total_memory,
            args.length,
            args.human_readable
        )
        return

    process_ids = pids_of_prog(args.program)
    if not process_ids:
        print(f"{args.program} not found.")
        return

    program_total = 0
    for process_id in process_ids:
        process_memory = rss_mem_of_pid(process_id)
        program_total += process_memory
        display_memory_line(
            process_id,
            process_memory,
            total_memory,
            args.length,
            args.human_readable
        )

    display_memory_line(
        args.program,
        program_total,
        total_memory,
        args.length,
        args.human_readable
    )


if __name__ == "__main__":
    main()
