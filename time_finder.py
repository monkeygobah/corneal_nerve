import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

class TimeFinder:
    """
    Identifies temperature drops in time-series data and allows for manual review and correction.
    """

    def __init__(self, data, dataname='default_name', output_dir='data_out', file_path='path', time_col="Time", temp_col="Temp",
                 detect_hot_points=False, neighbor_threshold=5, preced_window=30, 
                 drop_factor=1.5, deriv_thresh=1):
        
        self.file_path = file_path
        self.df = data

        # Ensure required columns exist
        if time_col not in self.df.columns:
            raise ValueError(f"Time column '{time_col}' not found in CSV.")
        if temp_col not in self.df.columns:
            raise ValueError(f"Temperature column '{temp_col}' not found in CSV.")

        self.time_col = time_col
        self.temp_col = temp_col
        self.detect_hot_points = detect_hot_points
        self.drop_points = []
        self.recovery_points = []

        # Hyperparameters
        self.neighbor_threshold = neighbor_threshold  
        self.preceding_window = preced_window    
        self.drop_threshold_factor = drop_factor 
        self.derivative_threshold = deriv_thresh if detect_hot_points else -1 * deriv_thresh

        # Output filenames
        self.base_filename = os.path.splitext(os.path.basename(file_path))[0]
        self.original_plot = f"{self.base_filename}_original.png"
        self.detected_plot = f"{self.base_filename}_drops.png"
        self.modified_plot = f"{self.base_filename}_drops_modified.png"
        self.output_dir = output_dir
        self.dataname = dataname[:-4]

        if not os.path.exists (self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.exists (os.path.join(self.output_dir, self.dataname)):
            os.makedirs(os.path.join(self.output_dir, self.dataname))
        self.save_dir = os.path.join(self.output_dir, self.dataname)

    def detect_drops(self, user_confirmation, plot_after):
        """Detects temperature drops and identifies recovery points."""
        temp_series = self.df[self.temp_col].values
        time_series = self.df[self.time_col].values

        # Compute first derivative
        dT_dt = np.gradient(temp_series, time_series)

        # Identify potential drop points (or hot peaks)
        drop_candidates = np.where(dT_dt > self.derivative_threshold)[0] if self.detect_hot_points else np.where(dT_dt < self.derivative_threshold)[0]

        if len(drop_candidates) == 0:
            print("No drops detected!")
            return

        # Cluster drop points
        clusters = []
        current_cluster = [drop_candidates[0]]

        for i in range(1, len(drop_candidates)):
            if drop_candidates[i] - drop_candidates[i - 1] <= self.neighbor_threshold:
                current_cluster.append(drop_candidates[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [drop_candidates[i]]
        clusters.append(current_cluster)  # Append last cluster

        # Identify refined drop points and recoveries
        refined_drops = []
        recoveries = []

        for cluster in clusters:
            if not cluster:
                continue

            # Define preceding region for baseline calculation
            start_index = max(0, cluster[0] - self.preceding_window)
            preceding_values = temp_series[start_index:cluster[0]]

            # Compute baseline fluctuation
            baseline_fluctuation = np.mean(np.abs(np.diff(preceding_values)))

            # Find the first point in the cluster where the drop is significant
            drop_index = None
            for idx in cluster:
                if abs(dT_dt[idx]) > self.drop_threshold_factor * baseline_fluctuation:
                    refined_drops.append(idx - 1)  # FIXED: Correcting off-by-one error
                    drop_index = idx
                    break  # Stop after first significant drop

            # Identify recovery: Find where derivative flips sign
            if drop_index is not None:
                for idx in range(drop_index + 1, len(dT_dt) - 1):
                    if (dT_dt[idx] > 0 and not self.detect_hot_points) or (dT_dt[idx] < 0 and self.detect_hot_points):
                        recoveries.append(idx - 1)  # FIXED: Correcting off-by-one error
                        break  # Stop at first recovery point

        # Store results in time values
        self.drop_points = list(time_series[refined_drops]) if refined_drops else []
        self.recovery_points = list(time_series[recoveries]) if recoveries else []

        # **PLOT DETECTED DROPS BEFORE ASKING FOR MANUAL CORRECTION**
        if user_confirmation:
            self.plot_results(self.detected_plot, show=True)

            # **Apply manual correction**
            self.drop_points = self.manual_correction(self.drop_points, "Drop Start")
            self.recovery_points = self.manual_correction(self.recovery_points, "Recovery")

        if plot_after:
        # **Replot modified points**
            self.plot_results(self.modified_plot, show=True)

    def manual_correction(self, points, label):
        """Allows manual correction of detected drop or recovery points."""
        print(f"\nDetected {label} points:", points)
        correction = input(f"Modify {label} points? (Enter: 'add time', 'remove time', or 'done')\n")

        while correction.lower() != "done":
            try:
                action, value = correction.split()
                value = float(value)

                if action == "add":
                    points.append(value)
                elif action == "remove":
                    points = [p for p in points if p != value]
                else:
                    print("Invalid command. Use 'add `time`' or 'remove `time`'.")
            except:
                print("Invalid input. Format: 'add `time`' or 'remove `time`'.")

            print(f"Updated {label} points:", points)
            correction = input(f"Modify {label} points? (Enter: 'add time', 'remove time', or 'done')\n")

        return sorted(points)  # Ensure points remain in time order

    def plot_results(self, savepath, show=False):
        """Plots detected drop/recovery points and saves the figure."""
        plt.figure(figsize=(10, 5))
        plt.plot(self.df[self.time_col], self.df[self.temp_col], marker='o', linestyle='-', alpha=0.6, label='Temperature')

        if len(self.drop_points) > 0:
            plt.scatter(self.drop_points, self.df.loc[self.df[self.time_col].isin(self.drop_points), self.temp_col], 
                        color='red', label='Drop Start', zorder=3)

        if len(self.recovery_points) > 0:
            plt.scatter(self.recovery_points, self.df.loc[self.df[self.time_col].isin(self.recovery_points), self.temp_col], 
                        color='green', label='Recovery', zorder=3)

        plt.xlabel("Time")
        plt.ylabel("Temperature")
        plt.title("Temperature Drop & Recovery Detection")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(self.save_dir, savepath), dpi=300)

        if show:
            plt.show()
        else:
            plt.close()

    def run_analysis(self, plot_orig,user_confirmation, plot_after):
        """Runs the complete analysis process."""
        # Step 1: Plot original temperature data
        if plot_orig:
            self.plot_results(self.original_plot, show=True)

        # Step 2: Detect peaks
        self.detect_drops(user_confirmation, plot_after)

        # Step 3: Return summary
        return {
            "num_drops": len(self.drop_points),
            "drop_times": self.drop_points,
            "recovery_times": self.recovery_points
        }
