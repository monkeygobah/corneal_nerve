# Electrophysiolic Analysis Toolkit

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

![6015 nw-2-25_frequency](https://github.com/user-attachments/assets/93b3e572-824a-4a4f-b2f6-9aacb9657a9e)

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
  - 
![6015 nw-2-25_events](https://github.com/user-attachments/assets/a962cf2d-b806-406c-b1d1-42f085a73e7d)
![6001 nw-2-05_events](https://github.com/user-attachments/assets/e2b748f4-4897-411e-8b18-9a2184494093)

## Usage
To run the analysis on a dataset:
```bash
python main_analysis.py
```
You will be prompted for manual correction of detected drops before final analysis.

