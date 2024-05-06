import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tqdm import tqdm
import linecache
import os
from tkinterdnd2 import DND_FILES, TkinterDnD


def generate_gcode(filename, layer_num, output_filename):
    total_lines = sum(1 for line in open(filename))  # get total lines of the file for the progress bar

    # Find the line number where the specified layer starts and where the header ends
    start_line = 0
    header_end_line = 0
    for i in tqdm(range(total_lines), desc='Reading the file'):  # add a progress bar
        line = linecache.getline(filename, i+1)
        if line.startswith(';LAYER:{}'.format(layer_num)):
            start_line = i
            break
        if line.startswith(';LAYER_COUNT'):
            header_end_line = i

    # Get the last E, Z, X, and Y values before the specified layer
    last_e_value, last_z_value, last_x_value, last_y_value = '', '', '', ''
    for line in reversed(linecache.getlines(filename)[header_end_line:start_line]):
        if line.startswith('G1') and 'E' in line and not last_e_value:
            last_e_value = re.search('E(\d+\.\d+)', line).group(1)
        if 'Z' in line and not last_z_value:
            last_z_value = re.search('Z(\d+\.\d+)', line).group(1)
        if 'X' in line and not last_x_value:
            last_x_value = re.search('X(\d+\.\d+)', line).group(1)
        if 'Y' in line and not last_y_value:
            last_y_value = re.search('Y(\d+\.\d+)', line).group(1)
        if all([last_e_value, last_z_value, last_x_value, last_y_value]):
            break

    # Get the nozzle and bed temperature from the original file
    nozzle_temp = re.search('M104 S(\d+)', ''.join(linecache.getlines(filename)[:header_end_line]))
    nozzle_temp = nozzle_temp.group(1) if nozzle_temp else '0'
    bed_temp = re.search('M190 S(\d+)', ''.join(linecache.getlines(filename)[:header_end_line]))
    bed_temp = bed_temp.group(1) if bed_temp else '0'

    # Create a new gcode file
    with open(output_filename, 'w') as file:
        # Set the nozzle temperature and wait for it to reach the target
        file.write('M117 Start heating ...\n')
        file.write('M104 S{} ; Set the nozzle temperature\n'.format(nozzle_temp))
        file.write('M109 S{} ; Wait for the nozzle temperature to reach the target\n'.format(nozzle_temp))

        # Set the current Z position as zero
        file.write('M117 Unstuck Extruder\n')
        file.write('G92 Z0 ; Set the current Z position as zero\n')

        # Lift the nozzle
        file.write('G1 Z5 F3000 ; Lift the nozzle\n')  # lift the nozzle

        # Home the X and Y axes
        file.write('M117 Homing X/Y ...\n')
        file.write('G28 X Y ; Home the X and Y axes\n')
        file.write('M117 Homing Z ...\n')
        file.write('G28 Z ; Home the Z axis\n')

        # Add the header lines from the original file, skipping lines with M140, M190, M104, M109, G28 X0 Y0 and G28 Z0
        skip_strings = ['M140', 'M190', 'M104', 'M109', 'G28 X0 Y0', 'G28 Z0']
        for line in linecache.getlines(filename)[:header_end_line+1]:
            if any(s in line for s in skip_strings):
                continue
            file.write(line)

        file.write('M117 Resuming Z ...\n')
        # Move the extruder to the last Z positions before the specified layer
        file.write('G0 Z{} F3000; Move the extruder Z to the last position before the specified layer\n'.format(float(last_z_value) + 2))
        file.write('M117 Resuming X/Y ...\n')
        # Move the extruder to the last X, Y positions before the specified layer
        file.write('G0 X{} Y{}; Move the extruder X Y to the last position before the specified layer\n'.format(last_x_value, last_y_value))
        file.write('M117 Resuming Extruder ...\n')
        # Set the last E value
        file.write('G92 E{} ; Set the current extruder value\n'.format(last_e_value))
        file.write('M117 Resuming from {}...\n'.format(layer_num))
        # Write the rest of the gcode starting from the specified layer
        for i in tqdm(range(start_line, total_lines), desc='Writing the file'):  # add a progress bar
            line = linecache.getline(filename, i+1)
            file.write(line)

def browse_file():
    filename = filedialog.askopenfilename(initialdir="/", title="Select file",
                                        filetypes=(("gcode files", "*.gcode"), ("all files", "*.*")))
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, filename)

def generate():
    filename = file_path_entry.get()
    layer_num = layer_num_entry.get()
    output_filename = filename[:-6] + "_start" + layer_num + filename[-6:]
    generate_gcode(filename, int(layer_num), output_filename)
    messagebox.showinfo("Success", f"New gcode file has been saved as {output_filename}")

def drop(event):
    filepath = event.data
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, filepath)


root = TkinterDnD.Tk()
root.title("Gcode Resume print Gcode Generator")

tk.Label(root, text="Original gcode file:").grid(row=0, column=0)
file_path_entry = tk.Entry(root, width=50)
file_path_entry.grid(row=0, column=1)
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', drop)
browse_button = tk.Button(root, text="Browse", command=browse_file)
browse_button.grid(row=0, column=2)

tk.Label(root, text="Cut layer number:").grid(row=1)
layer_num_entry = tk.Entry(root)
layer_num_entry.grid(row=1, column=1)

generate_button = tk.Button(root, text="Generate", command=generate)
generate_button.grid(row=1, column=2)

root.mainloop()

