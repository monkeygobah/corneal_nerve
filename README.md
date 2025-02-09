# Electrophysiolic Analysis Toolkit

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
  - [Create and activate a conda environment](#1-create-and-activate-a-conda-environment)
  - [Install dependencies](#2-install-dependencies)
- [Data Format Requirements](#data-format-requirements)
  - [Required Columns](#required-columns)
  - [Neuronal Event Columns](#neuronal-event-columns)
  - [Frequency Columns](#frequency-columns)
  - [Additional Notes](#additional-notes)
- [Drop Finder Algorithm](#drop-finder-algorithm)
- [Hyperparameters](#hyperparameters)
  - [Drop Detection](#drop-detection)
  - [Basal Temperature Calculation](#basal-temperature-calculation)
  - [Post-Stimulus Analysis](#post-stimulus-analysis)
- [Effect of `force_basal_computation`](#effect-of-force_basal_computation)
- [Logic for Computing Windows](#logic-for-computing-windows)
- [Outputs](#outputs)
- [Usage](#usage)

## Overview
This tool analyzes temperature drops in time-series data and performs statistical analysis on neuronal event responses. It allows for:
- Automated detection of temperature drops.
- Manual correction of drop times via the terminal.
- Calculation of neuronal activity before, during, and after stimulation.
- Visualization of temperature trends and stimulation periods.

## Setup
### 1. Create and activate a conda environment
```bash
conda create --name drop_analysis python=3.8 -y
conda activate drop_analysis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

## Data Format Requirements

For the tool to function correctly, your input CSV file must follow a specific structure. Below are the required and optional columns:

### **Required Columns**
These columns must be present in the dataset:
- **Time (`Time`)**: A numerical column representing time in seconds.
- **Temperature (`Temp`)**: A numerical column containing temperature values recorded over time.

### **Neuronal Event Columns**
Each neuron must have its own column representing event counts over time. These columns:
- Should be **numerical** (integer counts of detected events).
- **Must not start with `"f-"`** (this is reserved for frequency data).

Example:
```csv
Time,Temp,Neuron1,Neuron2,Neuron3
0.0,36.5,2,1,3
0.5,36.4,1,0,2
1.0,36.3,3,1,4
```

### Frequency Columns

If frequency data is available, it must be included as separate columns with the same name as the corresponding neuron, prefixed with `f-`.

Example:

```csv
Time,Temp,Neuron1,Neuron2,Neuron3,f-Neuron1,f-Neuron2,f-Neuron3
0.0,36.5,2,1,3,5.2,4.1,6.0
0.5,36.4,1,0,2,5.0,4.0,5.8
1.0,36.3,3,1,4,5.3,4.2,6.1
```
Additional Notes
- All time values must be in ascending order.
- Ensure no missing values in the required columns (Time, Temp, and neuron columns).
- The tool automatically detects event columns by excluding Time, Temp, and any column prefixed with "f-".
- Frequency columns are linked to their respective neuron event columns by their prefix ("f-").

## Drop Finder Algorithm
The drop detection algorithm identifies temperature drops by computing the derivative of the temperature signal. It:
1. Identifies points where the temperature decreases rapidly.
2. Clusters nearby drops to avoid redundancy.
3. Uses a baseline fluctuation measure to filter significant drops.
4. Detects the recovery point where temperature starts to rise again.
5. **Allows manual correction**: After detecting drops, the user can modify drop times interactively in the terminal.

## Hyperparameters
### Drop Detection
- `neighbor_threshold`: The maximum time gap (in indices) for drop clustering.
- `preced_window`: Number of data points before a drop used for baseline fluctuation calculation.
- `drop_factor`: Factor multiplied by baseline fluctuation to determine a significant drop.
- `deriv_thresh`: The threshold for the derivative to classify a point as a drop.

![08202024_Intact_Cold_drops_modified](https://github.com/user-attachments/assets/b403299f-4d80-4690-8048-eab51a8641a6)

### Basal Temperature Calculation
- `window_before`: Time window (seconds) before a drop used to compute baseline temperature.
- `std_threshold`: Number of standard deviations below baseline mean temperature for defining recovery.

### Post-Stimulus Analysis
- `window_after`: Time window (seconds) after recovery used for post-stimulation analysis.

## Effect of `force_basal_computation`
- **Enabled (`True`)**: Always computes the basal temperature using the full `window_before`, regardless of temperature recovery.
- **Disabled (`False`)**: Adjusts the basal window dynamically to avoid overlap and handles cases where the temperature never recovers.

## Logic for Computing Windows
1. **Basal Period (`window_before`)**:
   - If `force_basal_computation` is **on**, always use the `window_before` before the drop.
   - Otherwise, basal computation is **adjusted** if the previous drop did not recover.
   - If necessary, truncates the basal window to prevent overlap.

2. **During Stimulus Period**:
   - Starts at the detected **response time**.
   - Ends when temperature recovers to the computed **recovery threshold**.
   - If recovery never happens, extends until the next drop or the end of the recording.

3. **After-Stimulation Period (`window_after`)**:
   - Starts when the temperature fully recovers.
   - If recovery never happens, no after-stimulus period is recorded.

## Outputs
- **Processed CSV (`analyzed_<filename>.csv`)**: 
  - Time windows for basal, during, and post-stimulation periods.
  - Computed statistics for neuronal events in each window.
  - Recovery threshold temperatures.
  - Flags indicating forced computations.

- **Failure Report (`failure_<filename>.csv`)**:
  - Counts of drops where the temperature never recovered.

- **Plots**:
  - **Annotated temperature plot** (`<filename>_temp.png`): Shows drop periods and recovery windows.
  - **Neuron event/frequency plots**: Highlights neuronal responses relative to detected drops.
    
![6001 nw-2-05_events](https://github.com/user-attachments/assets/e2b748f4-4897-411e-8b18-9a2184494093)
![6004 nw-2-12_frequency](https://github.com/user-attachments/assets/16d5c11b-9aac-457c-a8ca-824a04145dfc)

## Usage
To run the analysis on a dataset:
```bash
python main_analysis.py
```
You will be prompted for manual correction of detected drops before final analysis.

