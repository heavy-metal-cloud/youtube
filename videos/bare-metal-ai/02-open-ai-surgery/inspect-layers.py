#!/usr/bin/env python3
"""
safetensor_inspector.py

A script to inspect the layers of a .safetensors file without loading
the full model weights into memory. It reads the file header metadata,
parses it, and presents a summary of the available layers.

Usage:
    python safetensor_inspector.py --file path/to/model.safetensors [--verbose] [--output-format json|csv]

Author: AI Assistant
"""

import argparse
import json
import struct
import sys
from typing import Dict, Any, List


def get_dtype_size(dtype_str: str) -> int:
    """
    Maps safetensor dtype strings to their byte size.

    Args:
        dtype_str: String like 'F32', 'I64', 'F16', etc.

    Returns:
        Size in bytes (int). Returns 0 if unknown.
    """
    mapping = {
        "BF16": 2,
        "F8_E5M2": 1,
        "F8_E4M3": 1,
        "F16": 2,
        "F32": 4,
        "F64": 8,
        "I8": 1,
        "U8": 1,
        "I16": 2,
        "U16": 2,
        "I32": 4,
        "U32": 4,

        "I64": 8,
        "U64": 8,
    }
    # Normalize to uppercase for comparison (safetensors are usually upper)
    return mapping.get(dtype_str.upper(), 0)


def read_safetensor_metadata(filepath: str) -> Dict[str, Any]:
    """
    Reads the header of a safetensor file manually.

    The safetensor format is defined as:
    [Header Length (8 bytes, u64 LE)] + [JSON Metadata String]

    Args:
        filepath: Path to the .safetensors file

    Returns:
        Dictionary containing parsed metadata.

    Raises:
        ValueError: If the file format is invalid or header length mismatch.
    """
    try:
        with open(filepath, "rb") as f:
            # Read the first 8 bytes for header length (u64 little-endian)
            len_bytes = f.read(8)
            if len(len_bytes) != 8:
                raise ValueError("File too short to contain valid safetensor header.")

            header_len = struct.unpack("<Q", len_bytes)[0]

            # Read the JSON metadata string
            json_str_bytes = f.read(header_len)
            if len(json_str_bytes) != header_len:
                raise ValueError(f"Header length mismatch. Expected {header_len}, got {len(json_str_bytes)}.")

            return json.loads(json_str_bytes.decode("utf-8"))

    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{filepath}' was not found.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in header. Error: {e}")


def format_shape(shape: List[int]) -> str:
    """Formats a shape list into a readable string."""
    if not shape:
        return "[]"
    return " x ".join(str(dim) for dim in shape)


def inspect_safetensor(file_path: str, verbose: bool = False, output_format: str = 'text'):
    """
    Main logic to inspect the safetensor file.

    Args:
        file_path: Path to the file.
        verbose: If True, prints more detailed stats per layer.
        output_format: 'text' (default), 'json', or 'csv'.
    """
    try:
        metadata = read_safetensor_metadata(file_path)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Separate actual tensors from potential top-level metadata (like _metadata key)
    layers = []
    total_params = 0

    for key, info in metadata.items():
        if key.startswith("_"):
            continue

        dtype = info.get("dtype", "UNKNOWN")
        shape = info.get("shape", [])

        # Calculate parameters for this layer (elements count)
        params = 1
        try:
            for dim in shape:
                params *= int(dim)
        except (TypeError, ValueError):
            pass

        total_params += params

        layers.append({
            "name": key,
            "dtype": dtype,
            "shape": shape,
            "params": params,
            "bytes": params * get_dtype_size(dtype)
        })

    # Sort layers by name for consistent output
    layers.sort(key=lambda x: x["name"])

    if output_format == 'json':
        print(json.dumps({
            "file": file_path,
            "total_layers": len(layers),
            "total_parameters": total_params,
            "layers": layers
        }, indent=2))

    elif output_format == 'csv':
        print("layer_name,dtype,shape,params_bytes")
        for layer in layers:
            shape_str = format_shape(layer["shape"])
            print(f"{layer['name']},{layer['dtype']},{shape_str},{layer['params']}")

    else:  # text (default)
        print(f"\n{'='*80}")
        print(f"SAFETENSOR INSPECTOR - {file_path}")
        print(f"{'='*80}\n")

        if not layers:
            print("No tensor layers found in this file.")
            return

        # Header for table
        if verbose:
            headers = ["Layer Name", "Shape", "Dtype", "Params (Count)", "Est. Size"]
        else:
            headers = ["Layer Name", "Shape", "Dtype"]

        print(f"{' | '.join(headers):<100}")
        print("-" * 80)

        for layer in layers:
            if verbose:
                # Format size to KB/MB/GB automatically
                b = layer['bytes']
                if b >= 1e9:
                    size_str = f"{b / 1e9:.2f} GB"
                elif b >= 1e6:
                    size_str = f"{b / 1e6:.2f} MB"
                elif b >= 1000:
                    size_str = f"{b / 1000:.2f} KB"
                else:
                    size_str = f"{b} B"

                print(f"{layer['name']:<40} | {format_shape(layer['shape']):<15} | {layer['dtype']:>8} | {layer['params']:,} params | {size_str}")
            else:
                print(f"{layer['name']:<40} | {format_shape(layer['shape']):<15} | {layer['dtype']}")

        print("-" * 80)
        print(f"\nSummary:")
        print(f"Total Layers:     {len(layers)}")
        print(f"Total Parameters: {total_params:,}")

        # Estimate total size based on dtype
        total_bytes = sum(l['bytes'] for l in layers)
        if total_bytes >= 1e9:
            size_str = f"{total_bytes / 1e9:.2f} GB"
        elif total_bytes >= 1e6:
            size_str = f"{total_bytes / 1e6:.2f} MB"
        else:
            size_str = f"{total_bytes} B"

        print(f"Total Weight Size: {size_str}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the layers of a .safetensors file without loading weights into memory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file model.safetensors
  %(prog)s --file model.safetensors -v
  %(prog)s --file model.safetensors --output-format json
  %(prog)s --file model.safetensors --output-format csv > layers.csv
        """
    )

    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to the .safetensors file to inspect."
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show additional details: parameter count and estimated size per layer."
    )

    output_choices = ['text', 'json', 'csv']
    parser.add_argument(
        "--output-format",
        default='text',
        choices=output_choices,
        help=f"Output format. Supported: {', '.join(output_choices)} (default: text)"
    )

    args = parser.parse_args()

    # Validate output format argument is lowercase just in case
    args.output_format = args.output_format.lower()

    inspect_safetensor(args.file, verbose=args.verbose, output_format=args.output_format)


if __name__ == "__main__":
    main()