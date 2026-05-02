#!/usr/bin/env python3
"""
Independent Safetensor Weight Modification Verifier

Compares tensors from input and output safetensor files to verify
that weight modifications were successfully persisted.

Usage:
    python verify_changes.py \
        --input original.safetensors \
        --output modified.safetensors \
        --layer model.layers.0.self_attn.q_proj.weight
"""

import argparse
from safetensors import safe_open
import numpy as np
import sys


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify weight modifications between two safetensor files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i original.safetensors -o modified.safetensors -l "model.layers.0.weight"

  %(prog)s --input model-00001-of-00002.safetensors \\
           --output model-modified-00001-of-00002.safetensors \\
           --layer lm_head.weight
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        type=str,
        help="Path to the original input .safetensor file."
    )

    parser.add_argument(
        "--output", "-o",
        required=True,
        type=str,
        help="Path to the modified output .safetensor file."
    )

    parser.add_argument(
        "--layer", "-l",
        required=False,
        default=None,
        type=str,
        help="Layer name (tensor key) to verify. If not provided, will prompt user."
    )

    return parser.parse_args()


def list_available_layers(filepath: str) -> None:
    """Print all available layer names in a safetensor file."""
    try:
        with safe_open(filepath, framework="numpy") as f:
            keys = list(f.keys())
            print(f"\n📁 Available layers in {filepath} ({len(keys)} total):")
            for key in sorted(keys):
                tensor = f.get_tensor(key)
                print(f"  - {key:<60s} | Shape: {tensor.shape}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")


def verify_file_changes(input_path: str, output_path: str, layer_name: str) -> bool:
    """Compare tensors from input and output files directly."""

    print("\n🔍 Independent Verification Test")
    print("=" * 80)

    try:
        # Load BOTH files fresh (no caching)
        with safe_open(input_path, framework="numpy") as f_in:
            tensor_before = f_in.get_tensor(layer_name)

        with safe_open(output_path, framework="numpy") as f_out:
            tensor_after = f_out.get_tensor(layer_name)

    except KeyError as e:
        print(f"❌ Layer '{layer_name}' not found in one or both files!")
        return False
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        return False

    # Compare tensors element-by-element
    diff_mask = (tensor_before != tensor_after)
    changed_count = np.sum(diff_mask)
    total_elements = tensor_before.size

    pct_changed = (changed_count / total_elements * 100) if total_elements > 0 else 0

    print(f"Layer: {layer_name}")
    print(f"Dtype: {tensor_before.dtype}")
    print(f"Shape: {tensor_before.shape}")
    print("-" * 80)
    print(f"Elements Changed: {changed_count:,} / {total_elements:,}")
    print(f"Percentage Changed: {pct_changed:.2f}%")
    print("-" * 80)

    # Show sample of changed values
    if changed_count > 0:
        print("\n📊 Sample Changes (Before → After):")

        # Get indices where they differ
        diff_indices = np.where(diff_mask.flatten())[0]
        samples_to_show = min(10, len(diff_indices))

        for i in range(samples_to_show):
            idx = diff_indices[i]
            old_val = float(tensor_before.flatten()[idx])
            new_val = float(tensor_after.flatten()[idx])

            # Show multi-dimensional index
            multi_idx = np.unravel_index(idx, tensor_before.shape)
            print(f"  Index {multi_idx}: {old_val:>15.8f} → {new_val:>15.8f}")

    if pct_changed > 0:
        print("\n✅ SUCCESS: Weights WERE modified!")
        return True
    else:
        print("\n❌ FAILURE: No weight changes detected!")
        return False


def main():
    args = parse_arguments()

    # If no layer specified, prompt user or show available layers
    if not args.layer:
        print("⚠️  No layer name provided. Showing available layers from input file...")
        list_available_layers(args.input)
        print("\nPlease re-run with --layer or -l <layer_name>")
        sys.exit(1)

    # Run verification
    success = verify_file_changes(args.input, args.output, args.layer)

    if not success:
        print("\n💡 Tip: To see available layers in a file, run without --layer argument.")
        sys.exit(1)


if __name__ == "__main__":
    main()