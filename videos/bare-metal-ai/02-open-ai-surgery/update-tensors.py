#!/usr/bin/env python3
"""
Script to randomly modify weights in a .safetensors file with verbose output.
Supports both floating-point and quantized integer models.
Handles various safetensors versions and import paths.
"""

import argparse
import os
import sys
import numpy as np


def load_safetensors_module():
    """
    Attempt to import the safetensors module from different possible locations.
    Returns (safe_open, save_file) functions or raises ImportError.
    Ensures consistent return type of 2 values.
    """
    # Try standard import first (safetensors >= 0.3.x)
    try:
        from safetensors import safe_open as std_safe_open
        from safetensors import save_file as std_save_file

        def safe_open_wrapper(path, framework="numpy"):
            return std_safe_open(path, framework=framework)

        # Verify it works with context manager
        test_obj = std_safe_open(os.devnull, framework="numpy")
        if hasattr(test_obj, 'keys'):
            return std_safe_open, std_save_file
    except Exception:
        pass


    # Try alternative import path (safetensors.numpy for some environments)
    try:
        from safetensors.numpy import load_file as np_load_file
        from safetensors.numpy import save_file as np_save_file

        def safe_open_wrapper(path, framework="numpy"):
            return np_load_file(path)

        return safe_open_wrapper, np_save_file
    except ImportError:
        pass

    # Try MLX-compatible path (for LM Studio/MLX environments)
    try:
        from safetensors import load_file as mlx_load
        from safetensors import save_file as mlx_save

        def safe_open_wrapper(path, framework="numpy"):
            return mlx_load(path)

        return safe_open_wrapper, mlx_save
    except ImportError:
        pass

    # Fallback: try to find any working combination
    try:
        from safetensors import safe_open as fallback_safe_open
        from safetensors.numpy import save_file as fallback_save

        def safe_open_wrapper(path, framework="numpy"):
            return fallback_safe_open(path, framework=framework)

        return safe_open_wrapper, fallback_save
    except ImportError:
        pass

    raise ImportError(
        "\n\n❌ ERROR: safetensors library not found or incompatible.\n"
        "Please install it using:\n"
        "   pip install safetensors numpy\n\n"
        f"Current Python path: {sys.executable}\n"
        f"Python version: {sys.version}"
    )


def get_dtype_limits(dtype):
    """Returns min and max values for a numpy dtype."""
    if np.issubdtype(dtype, np.floating):
        return -np.inf, np.inf

    try:
        info = np.iinfo(dtype)
        return info.min, info.max
    except ValueError:
        return -np.inf, np.inf


def modify_weights_verbose(weights_dict, percentage, multiplier, verbose=True, max_print=50):
    """
    Iterate through tensors and randomly modify weights with optional verbose output.

    Args:
        weights_dict (dict): Dictionary of tensor names to numpy arrays.
        percentage (float): Percentage of total elements to modify (0-100).
        multiplier (float): Factor to multiply modified weights by.
        verbose (bool): Whether to print modification details.
        max_print (int): Maximum number of modifications to print in detail.

    Returns:
        dict: Modified weights dictionary with stats.
    """
    total_elements = sum(w.size for w in weights_dict.values())

    if percentage <= 0 or total_elements == 0:
        return weights_dict, {"total_modified": 0}

    target_modifications = int(total_elements * (percentage / 100.0))
    modified_count = 0

    print(f"\n{'='*60}")
    print(f"Starting weight modifications...")
    print(f"Total elements in model: {total_elements:,}")
    print(f"Target modifications: {target_modifications:,} ({percentage}%)")
    print(f"Multiplier: {multiplier}")
    print(f"{'='*60}\n")

    for name, tensor in weights_dict.items():
        original_dtype = tensor.dtype
        min_val, max_val = get_dtype_limits(original_dtype)

        flat_tensor = tensor.flatten()

        # Calculate how many to modify from this tensor
        remaining = target_modifications - modified_count
        elements_in_tensor = flat_tensor.size

        if remaining <= 0:
            break

        num_to_modify = min(remaining, elements_in_tensor)

        selected_indices = np.random.choice(elements_in_tensor, size=num_to_modify, replace=False)
        sorted_indices = np.sort(selected_indices)

        # Create a working copy of this tensor
        modified_tensor = np.array(tensor)

        print(f"\nTensor: {name}")
        print(f"  Shape: {tensor.shape}, Dtype: {original_dtype}")
        print(f"  Modifying {num_to_modify} out of {elements_in_tensor} elements...")

        for i, idx in enumerate(sorted_indices):
            original_value = modified_tensor.flat[idx]

            if original_dtype in [np.int8, np.uint8, np.int16, np.uint16,
                                  np.int32, np.uint32, np.int64, np.uint64]:
                # Integer Logic: Multiply and Clamp to valid range
                new_value = modified_tensor.flat[idx] * multiplier

                if min_val != -np.inf:
                    new_value = max(min_val, min(max_val, new_value))
                
                # Explicitly cast back to original integer dtype before assignment 
                # to ensure safe storage and prevent float artifacts.
                new_value = int(new_value) 

            else:
                # Float Logic: Just multiply
                new_value = modified_tensor.flat[idx] * multiplier

            modified_tensor.flat[idx] = new_value

            # Record modification details for verbose output
            if verbose and i < max_print:
                print(f"    [{i+1}] Index {idx}: {original_value} → {new_value}")

            elif verbose and i == max_print:
                print(f"    ... ({remaining - num_to_modify + 1} more modifications not shown)")

        weights_dict[name] = modified_tensor
        modified_count += len(sorted_indices)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Modification Complete!")
        print(f"Total elements modified: {modified_count:,}")
        print(f"Total elements in model: {total_elements:,}")
        print(f"Percentage modified: {(modified_count/total_elements)*100:.2f}%")
        print(f"{'='*60}\n")

    return weights_dict, {"total_modified": modified_count, "total_elements": total_elements}



def main():
    parser = argparse.ArgumentParser(
        description="Randomly modify weights in a safetensors file with verbose output.",
        epilog="""Examples:
  python update-tensors-4.py --input-file model.safetensors --output-file modified_model.safetensors --percentage 10 --multiplier 2
  python update-tensors-4.py -i model.safetensors -o modified_model.safetensors --quiet
"""
    )

    # Input/Output files (now with two dashes)
    parser.add_argument("--input-file", "-i", type=str, required=True,
                        help="Path to the input .safetensors file")
    parser.add_argument("--output-file", "-o", type=str, required=True,
                        help="Path to save the modified .safetensors file")

    # Modification parameters
    parser.add_argument("--percentage", type=float, default=10.0,
                        help="Percentage of total weights to modify (default: 10)")
    parser.add_argument("--multiplier", type=float, default=2.0,
                        help="Multiplier for weight modification magnitude (default: 2.0)")

    # Output control parameters
    parser.add_argument("--verbose", action="store_true", default=True,
                        help="Enable verbose output of modifications")
    parser.add_argument("--quiet", action="store_true",
                        help="Disable verbose output")
    parser.add_argument("--max-prints", type=int, default=50,
                        help="Maximum number of individual modification details to print (default: 50)")

    args = parser.parse_args()

    # Validate percentage range
    if not 0 <= args.percentage <= 100:
        print("Error: Percentage must be between 0 and 100.")
        sys.exit(1)

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    # Load safetensors module with compatibility check
    try:
        safe_open, save_file = load_safetensors_module()
        print("\n✓ Loaded safetensors successfully")

        # Test loading and handle different return types (context manager vs direct dict)
        test_obj = safe_open(args.input_file, framework="numpy")

        if isinstance(test_obj, dict):
            # Direct load (some versions return dict immediately)
            print("Using direct dictionary load mode")
            tensors = test_obj
            metadata = {}
        elif hasattr(test_obj, 'keys'):
            # Context manager mode (standard API)
            print("Using context manager load mode")
            with safe_open(args.input_file, framework="numpy") as f:
                if hasattr(f, 'metadata'):
                    metadata = f.metadata()
                else:
                    metadata = {}
                tensors = {key: f.get_tensor(key) for key in f.keys()}
        else:
            raise TypeError("Unexpected return type from safe_open")

    except Exception as e:
        print(f"\n❌ Error loading safetensors module or file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Warn user about risks
    if args.verbose and not args.quiet:
        print("⚠️  WARNING: Modifying weights will likely corrupt the model's functionality.")
        print("Ensure you have a backup of the original file.\n")

    verbose_output = args.verbose and not args.quiet

    # Perform modification
    modified_tensors, stats = modify_weights_verbose(
        tensors,
        args.percentage,
        args.multiplier,
        verbose=verbose_output,
        max_print=args.max_prints
    )

    # Save the modified model
    print(f"\nSaving to {args.output_file}...")
    try:
        save_file(modified_tensors, args.output_file, metadata=metadata)

        if verbose_output:
            print("\n" + "="*60)
            print("SUCCESS!")
            print("="*60)
            print(f"Output file: {args.output_file}")
            print(f"Elements modified: {stats['total_modified']:,} / {stats['total_elements']:,}")
            if stats['total_elements'] > 0:
                pct = (stats['total_modified'] / stats['total_elements']) * 100
                print(f"Modification rate: {pct:.2f}%")
            print("="*60 + "\n")
        else:
            print("Successfully saved modified safetensors file.")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

