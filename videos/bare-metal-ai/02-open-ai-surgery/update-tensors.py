#!/usr/bin/env python3
"""
LLM Safetensor Weight Modifier Tool - Verified Version

This script modifies weights within a .safetensor file based on specific criteria:
- Target layers (by name)
- Percentage of weights to modify per layer
- A multiplier modifier applied to selected weights
- Detailed logging with before/after weight examples

It is designed for experimentation and includes robust logging to track changes.
"""

import argparse
import sys
import logging
import numpy as np
from safetensors import safe_open
from safetensors.numpy import save_file
from typing import List, Dict, Tuple, Any

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Modify weights in an Open Weight LLM safetensor file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--input", "-i", required=True, type=str, help="Path to input .safetensor file.")
    parser.add_argument("--output", "-o", default=None, type=str, help="Output path. If not provided, overwrites input.")
    parser.add_argument("--layers", "-l", required=True, type=str, help="Comma-separated list of layer names to modify.")
    parser.add_argument("--percent", "-p", type=float, default=1.0, help="Percentage (0-100) of weights to change. Default: 1.0")
    parser.add_argument("--modifier", "-m", type=float, default=2.0, help="Multiplier applied to selected weights. Default: 2.0")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--samples-per-layer", "-n", type=int, default=5, help="Number of weight change examples per layer. Default: 5")

    return parser.parse_args()


def get_layer_stats(tensor: np.ndarray) -> Dict[str, Any]:
    stats = {
        "dtype": str(tensor.dtype),
        "shape": tensor.shape,
        "min": float(np.min(tensor)),
        "max": float(np.max(tensor)),
        "mean": float(np.mean(tensor)),
        "std": float(np.std(tensor))
    }
    return stats


def get_dtype_bounds(dtype: np.dtype) -> Tuple[float, float]:
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        return float(info.min), float(info.max)
    elif np.issubdtype(dtype, np.floating):
        return -np.inf, np.inf
    else:
        return 0.0, 100.0


def modify_tensor(tensor: np.ndarray, percent: float, modifier: float, dtype_bounds: Tuple[float, float]) -> Tuple[np.ndarray, List[int], int]:
    total_elements = tensor.size
    num_changes = int(np.ceil(total_elements * (percent / 100.0)))

    if num_changes == 0:
        return tensor, [], 0

    flat_indices = np.random.choice(total_elements, size=num_changes, replace=False)
    modified_values = tensor.flatten().copy().astype(np.float64)
    modified_values[flat_indices] *= modifier

    min_val, max_val = dtype_bounds
    if not np.isinf(min_val):
        modified_values = np.clip(modified_values, a_min=min_val, a_max=max_val)

    result_tensor = modified_values.astype(tensor.dtype).reshape(tensor.shape)
    return result_tensor, flat_indices.tolist(), num_changes


def log_weight_examples(layer_name: str, tensor_before: np.ndarray, tensor_after: np.ndarray, changed_flat_indices: List[int], modifier: float, sample_count: int = 5) -> None:
    if not changed_flat_indices:
        return

    original_shape = tensor_before.shape
    display_count = min(sample_count, len(changed_flat_indices))

    logger.info(f"📊 {display_count} Example Weight Changes for Layer '{layer_name}'")
    logger.info("-" * 70)
    logger.info(f"{'Index':<25} | {'Before Value':>15} | {'After Value':>15} | {'Change'}")
    logger.info("-" * 70)

    for i in range(display_count):
        flat_idx = changed_flat_indices[i]
        multi_dim_idx = np.unravel_index(flat_idx, original_shape)
        idx_str = str(multi_dim_idx)

        old_val = float(tensor_before.flatten()[flat_idx])
        new_val = float(tensor_after.flatten()[flat_idx])

        if abs(old_val) > 1e-10:
            pct_change = ((new_val - old_val) / abs(old_val)) * 100
            sign = "+" if new_val >= old_val else ""
            change_str = f"{sign}{pct_change:.2f}%"
        else:
            change_str = f"({new_val})"

        if len(idx_str) > 23:
            idx_display = f"...{idx_str[-17:]}"
        else:
            idx_display = idx_str

        logger.info(f"{idx_display:<25} | {old_val:>15.8f} | {new_val:>15.8f} | {change_str}")

    logger.info("-" * 70)


def verify_weights_changed(input_path: str, output_path: str, layer_name: str, percent: float, modifier: float):
    """Verify that weights were actually changed after saving."""
    try:
        with safe_open(input_path, framework="numpy") as f_in:
            tensor_before = f_in.get_tensor(layer_name)

        with safe_open(output_path, framework="numpy") as f_out:
            tensor_after = f_out.get_tensor(layer_name)

        diff_count = np.sum(tensor_before != tensor_after)
        total_elements = tensor_before.size
        pct_changed = (diff_count / total_elements * 100) if total_elements > 0 else 0

        logger.info(f"🔍 VERIFICATION: {layer_name}")
        logger.info(f"   Elements changed: {diff_count} / {total_elements} ({pct_changed:.2f}%)")

        if pct_changed < percent * 0.5:
            logger.warning("⚠️  WARNING: Fewer weights changed than expected!")
            return False

        logger.info("✅ VERIFIED: Weights were successfully modified and saved.")
        return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def main():
    args = parse_arguments()

    if args.seed is not None:
        np.random.seed(args.seed)
        logger.info(f"Random seed set to {args.seed}")

    requested_layers = [layer.strip() for layer in args.layers.split(',')]
    logger.info(f"Target layers specified: {requested_layers}")

    if not args.output or args.output == "":
        logger.warning("No output path provided. Overwriting input file.")
        args.output = args.input

    tensor_data = {}
    try:
        with safe_open(args.input, framework="numpy") as f:
            for key in f.keys():
                tensor_data[key] = f.get_tensor(key)
    except Exception as e:
        logger.error(f"Failed to load safetensor file. Error: {e}")
        sys.exit(1)

    available_layers = list(tensor_data.keys())
    found_layers = []
    missing_layers = []

    for req_layer in requested_layers:
        if req_layer in available_layers:
            found_layers.append(req_layer)
        else:
            matching_key = None
            for key in available_layers:
                if key.lower() == req_layer.lower():
                    matching_key = key
                    break
            if matching_key:
                found_layers.append(matching_key)
                logger.warning(f"Found via case-insensitive match: '{req_layer}' → '{matching_key}'")
            else:
                missing_layers.append(req_layer)

    if missing_layers:
        logger.warning(f"Requested layers not found: {missing_layers}")

    if not found_layers:
        logger.error("No valid target layers found. Exiting.")
        sys.exit(1)

    total_elements_processed = 0
    total_elements_changed = 0
    layer_reports = []

    for req_layer in requested_layers:
        real_layer_name = None
        if req_layer in available_layers:
            real_layer_name = req_layer
        else:
            for key in available_layers:
                if key.lower() == req_layer.lower():
                    real_layer_name = key
                    break

        if not real_layer_name or real_layer_name not in tensor_data:
            logger.warning(f"Skipping {req_layer} (no matching key found)")
            continue

        tensor_before = tensor_data[real_layer_name]
        stats_before = get_layer_stats(tensor_before)

        logger.info(f"\n🔧 Processing Layer: '{real_layer_name}'")
        logger.info(f"Layer Stats (Before): dtype={stats_before['dtype']}, shape={stats_before['shape']}")

        if np.issubdtype(tensor_before.dtype, np.integer):
            min_bound, max_bound = get_dtype_bounds(tensor_before.dtype)
            logger.warning(f"⚠️  Layer uses integer dtype ({tensor_before.dtype}). Values clipped to [{min_bound}, {max_bound}]")
        else:
            min_bound, max_bound = -np.inf, np.inf

        tensor_after, changed_indices, count = modify_tensor(tensor_before, args.percent, args.modifier, (min_bound, max_bound))

        # ✅ FIX: Assign modified tensor back to dictionary
        tensor_data[real_layer_name] = tensor_after

        stats_after = get_layer_stats(tensor_after)
        logger.info(f"Layer Stats (After): min={stats_after['min']:.6f}, max={stats_after['max']:.6f}")

        if changed_indices:
            log_weight_examples(real_layer_name, tensor_before, tensor_after, changed_indices, args.modifier, sample_count=args.samples_per_layer)

        total_elements_processed += tensor_before.size
        total_elements_changed += count

        layer_reports.append({
            "name": real_layer_name,
            "processed": tensor_before.size,
            "changed": count
        })

    logger.info(f"\n💾 Saving modified safetensor to: {args.output}")
    try:
        save_file(tensor_data, args.output)
        logger.info("✅ File saved successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to save file. Error: {e}")
        sys.exit(1)

    # Verify weights were actually changed
    if len(found_layers) > 0 and args.input != args.output:
        verify_weights_changed(args.input, args.output, found_layers[0], args.percent, args.modifier)

    print("\n" + "="*80)
    print("📈 EXPERIMENT SUMMARY REPORT")
    print("="*80)
    print(f"Input File:   {args.input}")
    print(f"Output File:  {args.output}")
    print(f"Modifier:     x{args.modifier:.2f}")
    print(f"Percent Changed: {args.percent}%")
    print("-"*80)

    for report in layer_reports:
        pct = (report['changed'] / report['processed']) * 100 if report['processed'] > 0 else 0
        status_icon = "✅" if pct <= args.percent + 5 else "⚠️"
        print(f"{status_icon} {report['name']:45s} | Processed: {report['processed']:8d} | Changed: {report['changed']:6d} ({pct:.2f}%)")

    total_pct = (total_elements_changed / total_elements_processed * 100) if total_elements_processed > 0 else 0
    print(f"{'TOTAL':^45s} | {total_elements_processed:8d} | {total_elements_changed:6d} ({total_pct:.2f}%)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()