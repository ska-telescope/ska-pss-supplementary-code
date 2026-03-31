import argparse
import struct
import yaml
import sys
from scipy.stats import chi2, norm

def int_to_hex(i):
    return hex(struct.unpack('<I', struct.pack('<I', int(i)))[0])[2:].zfill(8).upper()

def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])[2:].zfill(8).upper()

def pack_dual_16(val1, val2):
    """Packs two integers into a single 32-bit hex string."""
    packed_val = (val1 << 8) | val2 # Use << 16 if the gap is larger
    return f"{packed_val:08X}"

def calculate_address(tree, set_num, seed, harmonic):
    base = 0x01860000
    harmonic_space = 8
    seed_space = 16 * harmonic_space 
    set_space = 0x1000 
    tree_space = 0x2000
    
    addr = base + \
           ((tree) * tree_space) + \
           ((set_num) * set_space) + \
           ((seed) * seed_space) + \
           ((harmonic) * harmonic_space)
    return f"{addr:08X}"

def get_chi2_threshold(sigma_level, nharm, df_per_sample=2):
    prob = norm.cdf(sigma_level) 
    total_df = (nharm+1) * df_per_sample
    return chi2.ppf(prob, df=total_df)

def get_ctrl_overlap(args):
    return 2 * args.largest_filter

def get_fop_num_samps(args):
    new_bins = args.fft_seg_len - get_ctrl_overlap(args)
    freq_res = 1 / args.obs_duration 
    nbins_needed = args.max_harm_freq / freq_res
    int_segs = int(nbins_needed / new_bins)
    return new_bins * int_segs

def load_yaml(path):
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)['registers']
    except (FileNotFoundError, KeyError):
        print(f"Error: Could not load registers from {path}")
        sys.exit(1)

# --- Calculation Helpers ---

def get_ctrl_params(args, reg_map):
    
    lines = []
    for addr, val in reg_map.items():
        if val == "CALC_OVERLAP":
            lines.append(f"{addr} {int_to_hex(get_ctrl_overlap(args))}")
        elif val == "CALC_NUM_SAMPS":
            lines.append(f"{addr} {int_to_hex(get_fop_num_samps(args)-1)}")
        else:
            lines.append(f"{addr} {val}")
    return "\n".join(lines) + "\n"

def get_conv_params(args, reg_map):
    lines = []
    for addr, val in reg_map.items():
        if val == "CALC_LARGEST_FILTER":
            lines.append(f"{addr} {int_to_hex(args.largest_filter)}")
        else:
            lines.append(f"{addr} {val}")
    return "\n".join(lines) + "\n"

def get_hsum_params(args, reg_map):
    lines = []
    for addr, val in reg_map.items():
        if val == "CALC_LARGEST_FILTER":
            lines.append(f"{addr} {int_to_hex(args.largest_filter)}")
        elif val == "CALC_NUM_SEEDS":
            lines.append(f"{addr} {pack_dual_16(args.num_seeds - 1, args.num_seeds - 1)}")
        else:
            lines.append(f"{addr} {val}")
    return "\n".join(lines) + "\n"

def get_thresholds_block(sigma):
    """Calculates and formats the threshold memory map."""
    lines = []
    for tree in range(2):
        for set_idx in range(2):
            for seed in range(21):
                for harm in range(16):
                    addr = calculate_address(tree, set_idx, seed, harm)
                    if harm < 8:
                        value = float_to_hex(get_chi2_threshold(sigma, harm))
                    else:
                        value = float_to_hex(0.0)
                    lines.append(f"{addr} {value}")
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate FPGA FDAS Configuration")
    parser.add_argument("hsum_config", help="Input HSUM config file path")
    parser.add_argument("sigma", type=float, help="Sigma level")
    parser.add_argument("--obs_duration", type=float, default=536.870912)
    parser.add_argument("--largest_filter", type=int, default=168)
    parser.add_argument("--fft_seg_len", type=int, default=1024)
    parser.add_argument("--max_harm_freq", type=int, default=4200)
    parser.add_argument("--num_seeds", type=int, default=12)

    args = parser.parse_args()

    # Load Register Maps
    ctrl_map = load_yaml('control_params.yaml')
    conv_map = load_yaml('conv_params.yaml')
    hsum_map = load_yaml('hsum_params.yaml')

    output_file = "Complete_FPGA_FDAS_config.txt"
    
    with open(output_file, 'w') as f_out:
        f_out.write(get_ctrl_params(args, ctrl_map))
        f_out.write(get_conv_params(args, conv_map))
        f_out.write(get_hsum_params(args, hsum_map))
        
        # Append the external HSUM file
        with open(args.hsum_config, 'r') as f_in:
            f_out.write(f_in.read())
        
        f_out.write("\n")
        f_out.write(get_thresholds_block(args.sigma))

    print(f"Configuration written to {output_file}")