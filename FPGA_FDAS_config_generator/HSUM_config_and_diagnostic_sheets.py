import numpy as np
import pandas as pd

# 1. Base Data Setup
filter_spacing = 4
filters1 = [i * filter_spacing for i in range(0, 43)]

filters = np.array(filters1)

filter_pos_values=['0x00','0x02','0x04','0x06','0x08','0x0A','0x0C','0x0E','0x12','0x14','0x16','0x18','0x1A','0x1C','0x1E','0x22','0x24','0x26','0x28','0x2A','0x2C','0x2E','0x32','0x34','0x36','0x38','0x3A','0x3C','0x3E','0x42','0x44','0x46','0x48','0x4A','0x4C','0x4E','0x52','0x54','0x56','0x58','0x5A','0x5C','0x5E']
filter_neg_values=['0x01','0x03','0x05','0x07','0x09','0x0B','0x0D','0x0F','0x13','0x15','0x17','0x19','0x1B','0x1D','0x1F','0x23','0x25','0x27','0x29','0x2B','0x2D','0x2F','0x33','0x35','0x37','0x39','0x3B','0x3D','0x3F','0x43','0x45','0x47','0x49','0x4B','0x4D','0x4F','0x53','0x55','0x57','0x59','0x5B','0x5D','0x5F']

# 2. Logic Functions
def return_addr(summer1, run1, seed1, slope1, harmonic1):
    addr = hex(int(0x1800000) + summer1*131072 + run1*65536 + seed1*2048 + slope1*128 + harmonic1*8)
    return '0' + addr.split('x')[1].upper()

def return_W(p):
    return filters[p] if 0 < p < len(filters) else 0

def Nslopes(harm):
    return [1, 3, 3, 5, 5, 7, 7, 9][harm-1]

def Nharms(seed_width, highest_width):
    for i in range(2, 9):
        if i * seed_width > highest_width: return i - 1
    return 8

def return_index(i, j, p, amb0):
    if j == 0: return p
    picks = [1, 3, 3, 5, 5, 7, 7, 9]
    max_range = (picks[j] - 1) // 2
    max_range0 = (amb0 - 1) // 2
    indices = np.arange(-max_range0, max_range0 + 1)
    offset = np.clip(indices[i], -max_range, max_range)
    return int(np.clip(p + offset, 0, len(filters) - 1))

def export_sheet(data, filename):
    df = pd.DataFrame(data, columns=columns)
    df.insert(0, 'Group_ID', group_ids)
    df.insert(1, 'Slope', slopes_labels)
    df.insert(2, 'Seed_Index', final_seeds)
    df.to_excel(filename, index=False)

# 3. Data Generation
stream_idx, stream_v1, stream_v2, stream_wid, stream_seeds = [], [], [], [], []
used_slopes = 0
max_width = 0
for p0 in range(1, len(filters)):
    perr = filter_spacing
    harms = Nharms(filters[p0], filters[-1])
    amb_slopes = Nslopes(harms)

    filts = [np.argmin(np.abs(filters - (j * (filters[p0] - perr/2.0)))) for j in range(1, harms + 1)]

    for i in range(amb_slopes):
        used_slopes += 1
        r_idx, r_v1, r_v2, r_wid = [], [], [], []
        for j in range(8):
            if j < harms:
                idx = return_index(i, j, filts[j], amb_slopes)
                r_idx.append(idx)
                r_v1.append(filter_pos_values[idx])
                r_v2.append(filter_neg_values[idx])
                r_wid.append(filters[idx])
                max_width = filters[idx]
            else:
                r_idx.append(np.nan)
                r_v1.append('0x60')
                r_v2.append('0x60')
                r_wid.append(np.nan)
        
        stream_idx.append(r_idx)
        stream_v1.append(r_v1)
        stream_v2.append(r_v2)
        stream_wid.append(r_wid)
        stream_seeds.append(p0)
        
# --- MANUAL ADDITION: The Largest Filter (Index 42, Width 168), as the last calculation in the above loop return second last fitler ---
used_slopes += 1
max_idx = 42 
stream_idx.append([max_idx] + [np.nan]*7)
stream_v1.append([filter_pos_values[max_idx]] + ['0x60']*7)
stream_v2.append([filter_neg_values[max_idx]] + ['0x60']*7)
stream_wid.append([filters[max_idx]] + [np.nan]*7)
stream_seeds.append(max_idx)
# 4. Normalizing and Padding (21 Groups x 11 Slopes = 231 rows)
target_total = 231
active_rows = used_slopes
print(active_rows)

# Ensure stream is long enough for active rows
while len(stream_v1) < active_rows:
    stream_v1.append(['0x60']*8); stream_v2.append(['0x60']*8)
    stream_idx.append([np.nan]*8); stream_wid.append([np.nan]*8)
    stream_seeds.append(np.nan)

# Create final structures
final_v1 = stream_v1[:active_rows] + [['0x60']*8] * (target_total - active_rows)
final_v2 = stream_v2[:active_rows] + [['0x60']*8] * (target_total - active_rows)
final_idx = stream_idx[:active_rows] + [[np.nan]*8] * (target_total - active_rows)
final_wid = stream_wid[:active_rows] + [[np.nan]*8] * (target_total - active_rows)
final_seeds = stream_seeds[:active_rows] + [np.nan] * (target_total - active_rows)

# 5. Export Individual Layout Sheets
columns = [f'H{i+1}' for i in range(8)]
group_ids = [i//11 + 1 for i in range(target_total)]
slopes_labels = list(range(1, 12)) * 21

export_sheet(final_v1, 'HPSEL_Layout_Summer1_Hex.xlsx')
export_sheet(final_v2, 'HPSEL_Layout_Summer2_Hex.xlsx')
export_sheet(final_idx, 'HPSEL_Layout_Indices.xlsx')
export_sheet(final_wid, 'HPSEL_Layout_Widths.xlsx')

# 6. Final Mapping and Address list
combined_data, txt_entries = [], []
for summer in range(2):
    current_hex = final_v1 if summer == 0 else final_v2
    for run in range(2):
        for g in range(21):
            for s in range(11):
                r_idx = (g * 11) + s
                for h in range(8):
                    addr = return_addr(summer, run, g, s, h)
                    val = str('000000')+current_hex[r_idx][h].split('x')[1]
                    f_idx = final_idx[r_idx][h]
                    f_wid = final_wid[r_idx][h]
                    
                    combined_data.append({
                        'Summer': summer, 'Run': run, 'Group_ID': g+1, 'Slope': s+1, 'Harmonic': h+1,
                        'Filter_Index': f_idx, 'Actual_Width': f_wid, 'Address': addr, 'Hex_Value': val
                    })
                    txt_entries.append(f"{addr} {val}")
with open("HSUM_config_address_value_list.txt", 'w') as f: f.write('\n'.join(txt_entries))
pd.DataFrame(combined_data).to_excel("Comprehensive_Hardware_Mapping.xlsx", index=False)