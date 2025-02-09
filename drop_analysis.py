from time_finder import TimeFinder
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os



class DropAnalysis:
    def __init__(self, df, drop_times, recovery_times, dataname='default_name', time_col="Time", temp_col="Temp",
                 window_before=30, window_after=30, std_threshold=2, save_plots=True, output_dir="plots",
                 force_basal_computation=False):
        """
        Initializes DropAnalysis for neuron event and frequency analysis.
        """
        self.df = df
        self.drop_times = [float(t) for t in drop_times]  
        self.recovery_times = [float(t) for t in recovery_times]
        self.time_col = time_col
        self.temp_col = temp_col
        self.window_before = window_before
        self.window_after = window_after
        self.std_threshold = std_threshold
        self.force_basal_computation = force_basal_computation  
        self.results = []
        self.drop_failure_counts = {}  
        self.save_plots = save_plots
        self.output_dir = output_dir
        self.dataname = dataname[:-4]

        if not os.path.exists (self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.exists (os.path.join(self.output_dir, self.dataname)):
            os.makedirs(os.path.join(self.output_dir, self.dataname))

        # Identify neuron event and frequency columns dynamically
        self.neuron_columns = [col for col in df.columns if not col.startswith("f-") and col not in [self.time_col, self.temp_col]]
        self.frequency_columns = {col: freq_col for col in self.neuron_columns for freq_col in df.columns if freq_col.startswith(f"f-{col}")}

    def analyze_drops(self):
        """Analyzes neuronal event data before, during, and after each drop and generates plots."""
        prev_full_recovery_time = None  # Track previous drop's full recovery time
        drop_intervals = []
        self.drop_failure_counts = {neuron: 0 for neuron in self.neuron_columns} 
        forced_computations = [] 
        recovery_failures = []

        for i, (drop_time, response_time) in enumerate(zip(self.drop_times, self.recovery_times)):
            drop_info = {"Drop #": i + 1}

            # **Determine Basal Start Time**
            basal_start = max(0, drop_time - self.window_before)
            '''
            Need to incorporate forced basal computation in here
            '''
            if self.force_basal_computation:
                # **Force Basal Computation: Always Use Window Before Drop**
                basal_start = max(0, drop_time - self.window_before)
                forced_basal_handling = "global"  # Mark global forced computation
            else:
                # **Standard Behavior: Adjust for Previous Recovery**
                basal_start = max(0, drop_time - self.window_before)

                # **Handle the first drop separately**
                # **Handle the first drop separately**
                if i == 0:
                    basal_start = max(0, drop_time - self.window_before)
                    forced_basal_handling = None  # No special handling for first drop
                else:
                    # **Case 1: If previous drop never fully recovered, reset basal_start to drop_time**
                    if prev_full_recovery_time is None or prev_full_recovery_time >= drop_time:
                        basal_start = drop_time
                        forced_basal_handling = "no_recovery"  # Special case for missing recovery

                    # **Case 2: Overlap prevention required**
                    elif prev_full_recovery_time and basal_start < prev_full_recovery_time:
                        basal_start = prev_full_recovery_time  # Prevent overlap
                        forced_basal_handling = "overlap_prevention"  # Prevented overlap

                    # **Case 3: Normal basal period calculation (at least `window_before` available)**
                    else:
                        basal_start = max(0, drop_time - self.window_before)
                        forced_basal_handling = None  # No forced computation, normal green shade


            forced_computations.append(forced_basal_handling)  # Store forced computation type



            # **Compute Basal Temperature Mean & STD (Always Computed)**
            basal_segment = self.df[(self.df[self.time_col] >= basal_start) & (self.df[self.time_col] < drop_time)]
            forced_basal = False  
            temp_threshold = None  

            if basal_segment.empty:
                # **If no valid basal period, use drop-time temperature**
                temp_threshold = self.df.loc[self.df[self.time_col] == drop_time, self.temp_col].values[0]
                print('EMPTY')
                print(temp_threshold, print(type(temp_threshold)))
            else:
                basal_temp_mean = basal_segment[self.temp_col].mean()
                basal_temp_std = basal_segment[self.temp_col].std()
                temp_threshold = basal_temp_mean - self.std_threshold * basal_temp_std 
                # print(temp_threshold, print(type(temp_threshold)))


            # **Find Full Recovery Time (First Time Temp Returns to Basal)**
            temp_after_recovery = self.df[self.df[self.time_col] >= response_time]
            reached_threshold = False  # Track if temperature fully recovered
            full_recovery_time = None  # Track actual recovery
            next_drop_time = self.drop_times[i + 1] if i + 1 < len(self.drop_times) else self.df[self.time_col].max()

            for idx, row in temp_after_recovery.iterrows():
                if temp_threshold is not None and row[self.temp_col] >= temp_threshold:
                    if row[self.time_col] < next_drop_time:  #  Only valid if recovery happens before the next drop
                        full_recovery_time = row[self.time_col]
                        reached_threshold = True
                        break  # Stop at first valid recovery


            # **If Temperature Never Recovers, Use Next Drop or Max Time**
            if full_recovery_time is None:
                full_recovery_time = self.drop_times[i + 1] if i + 1 < len(self.drop_times) else self.df[self.time_col].max()
                print(full_recovery_time)


            # **Update Failure Count for Neurons**
            if not reached_threshold:
                for neuron in self.neuron_columns:
                    self.drop_failure_counts[neuron] += 1


            # **After Stim Period (Only If Recovery Occurred)**
            if reached_threshold:
                after_start = full_recovery_time
                after_end = after_start + self.window_after
                if i + 1 < len(self.drop_times) and after_end > self.drop_times[i + 1]:
                    after_end = self.drop_times[i + 1]
                recovery_failures.append(False)  

            else:
                after_start = None
                after_end = None
                recovery_failures.append(True)  

            # **Store Drop Information**
            drop_info["30s Before"] = f"{basal_start} to {drop_time}"
            drop_info["During Stim"] = f"{response_time} to {full_recovery_time}"
            drop_info["30s After"] = f"{after_start} to {after_end}"
            drop_info["Forced Basal"] = forced_basal_handling

            # **Store Temperature Data for Each Drop**
            drop_info["Basal Temp ± STD"] = f"{basal_temp_mean:.3f} ± {basal_temp_std:.3f}" if basal_temp_mean is not None else "N/A"
            drop_info["Min Temp (Response Time)"] = f"{self.df.loc[self.df[self.time_col] == response_time, self.temp_col].values[0]:.3f}" if response_time in self.df[self.time_col].values else "N/A"
            drop_info["Recovery Threshold Temp"] = f"{temp_threshold:.3f}" 

            drop_intervals.append((basal_start, drop_time, response_time, full_recovery_time, after_start, after_end))

            # **Compute Stats for Each Neuron**
            for neuron in self.neuron_columns:
                basal_stats = self.compute_segment_stats(basal_start, drop_time, neuron)
                during_stats = self.compute_segment_stats(response_time, full_recovery_time, neuron) if reached_threshold else {"Event Mean ± STD": "N/A", "Freq Mean ± STD": "N/A"}
                after_stats = self.compute_segment_stats(after_start, after_end, neuron)

                drop_info.update({
                    f"{neuron} - Basal Period": basal_stats["Event Mean ± STD"],
                    f"{neuron} - During": during_stats["Event Mean ± STD"],
                    f"{neuron} - After Resolution": after_stats["Event Mean ± STD"],

                    f"{neuron} - Basal Period Freq": basal_stats["Freq Mean ± STD"],
                    f"{neuron} - During Freq": during_stats["Freq Mean ± STD"],
                    f"{neuron} - After Resolution Freq": after_stats["Freq Mean ± STD"],
                })

            self.results.append(drop_info)
            prev_full_recovery_time = full_recovery_time  # Update for next iteration


        # **Save Results to CSV**
        results_df = pd.DataFrame(self.results)
        failure_counts_df = pd.DataFrame(list(self.drop_failure_counts.items()), columns=["Neuron", "Failure Count"])

        # **Generate Plots**
        if self.save_plots:
            self.plot_temp_with_annotations(drop_intervals, forced_computations,recovery_failures)
            for neuron in self.neuron_columns:
                self.plot_neuron(neuron, drop_intervals, f"{neuron}_events", forced_computations,recovery_failures)
                if neuron in self.frequency_columns:
                    freq_neuron = self.frequency_columns[neuron]
                    self.plot_neuron(freq_neuron, drop_intervals, f"{neuron}_frequency", forced_computations,recovery_failures)

        # Save results to CSV
        result_name = os.path.join(self.output_dir, self.dataname, 'analyzed_'+ self.dataname +'.csv')
        results_df.to_csv(result_name, index=False)

        failure = os.path.join(self.output_dir, self.dataname, 'failure_'+ self.dataname +'.csv')
        failure_counts_df.to_csv(failure, index=False)


    def compute_segment_stats(self, start_time, end_time, neuron_col):
        """Computes mean ± std for neuron event count and frequency in a given time window."""
        segment = self.df[(self.df[self.time_col] >= start_time) & (self.df[self.time_col] < end_time)]
        stats = {}

        event_mean = segment[neuron_col].mean() if neuron_col in segment.columns else None
        event_std = segment[neuron_col].std() if neuron_col in segment.columns else None
        stats["Event Mean ± STD"] = self.format_stats(event_mean, event_std)

        freq_col = self.frequency_columns.get(neuron_col, None)
        if freq_col and freq_col in segment.columns:
            freq_mean = segment[freq_col].mean()
            freq_std = segment[freq_col].std()
            stats["Freq Mean ± STD"] = self.format_stats(freq_mean, freq_std)
        else:
            stats["Freq Mean ± STD"] = "N/A"

        return stats

    @staticmethod
    def format_stats(mean, std):
        """Formats statistics as 'mean ± std' and handles missing values gracefully."""
        return f"{mean:.3f} ± {std:.3f}" if pd.notna(mean) and pd.notna(std) else "N/A"


    def plot_temp_with_annotations(self, drop_intervals, forced_computations, recovery_failures):
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot temperature over time
        ax.plot(self.df[self.time_col], self.df[self.temp_col], color='blue', alpha=0.7, label="Temperature")

        for idx, (basal_start, drop_time, during_start, during_end, after_start, after_end) in enumerate(drop_intervals):
            # **Determine Hatching Style for Forced Computation in Green (Basal Period)**
            forced_type = forced_computations[idx]
            hatch_style = None
            if forced_type == "no_recovery":
                hatch_style = "oo"  # No full recovery, so basal temp was forced
            elif forced_type == "overlap_prevention":
                hatch_style = "//"  # Overlap prevention adjusted the basal window

            # **Always show green (30s Before window), with hatching only if required**
            ax.axvspan(basal_start, drop_time, color='green', alpha=0.2, hatch=hatch_style, label="30s Before" if idx == 0 else "")

            # **Determine Hatching Style for Red (During Stim) if No Recovery**
            stim_hatch = "\\" if recovery_failures[idx] else None  
            
            # **Always show red (During Stim window), with hatching if no recovery**
            ax.axvspan(during_start, during_end, color='red', alpha=0.3, hatch=stim_hatch, label="During Stim" if idx == 0 else "")

            # **Only plot after-period if it exists**
            if after_start is not None and after_end is not None:
                ax.axvspan(after_start, after_end, color='purple', alpha=0.2, label="30s After" if idx == 0 else "")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("Temperature Drops and Stimulation Periods")
        ax.legend()
        
        plt.savefig(os.path.join(self.output_dir, self.dataname, f"{self.dataname}_temp.png"), dpi=300)
        plt.close()

    def plot_neuron(self, neuron, drop_intervals, plot_label, forced_computations, recovery_failures):
        """
        Plots neuron event or frequency data with stim periods and saves them.
        If force_basal_computation=True for a drop, the 30s Before window is still displayed but with hatching.
        """
        fig, ax = plt.subplots(figsize=(10, 5))

        is_frequency = neuron in self.frequency_columns.values()  # Check if it's a frequency plot
        
        if is_frequency:
            # **Plot frequency data as a continuous line**
            ax.plot(self.df[self.time_col], self.df[neuron], label=f"{neuron} {plot_label}", color='blue')
        else:
            # **Plot event counts as a histogram**
            ax.hist(self.df[self.time_col], bins=50, weights=self.df[neuron], alpha=0.7, color='black', label=f"{neuron} {plot_label}")

        for idx, (basal_start, drop_time, during_start, during_end, after_start, after_end) in enumerate(drop_intervals):
            # **Determine Hatching Style for Forced Computation**
            forced_type = forced_computations[idx]
            hatch_style = None  # Default: No hatching

            if forced_type == "no_recovery":
                hatch_style = "oo"  # No full recovery, basal temp was forced
            elif forced_type == "overlap_prevention":
                hatch_style = "//"  # Overlap prevention adjusted the basal window

            # **Always show green (30s Before window), with hatching if forced**
            ax.axvspan(basal_start, drop_time, color='green', alpha=0.2, hatch=hatch_style, label="30s Before" if idx == 0 else "")

            # **Only plot after-period if it exists**
            if after_start is not None and after_end is not None:
                ax.axvspan(after_start, after_end, color='purple', alpha=0.2, label="30s After" if idx == 0 else "")

            stim_hatch = "\\" if recovery_failures[idx] else None  

            # **Always show red (During Stim window), with hatching if no recovery**
            ax.axvspan(during_start, during_end, color='red', alpha=0.3, hatch=stim_hatch, label="During Stim" if idx == 0 else "")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Neuron Events" if not is_frequency else "Frequency (Hz)")
        ax.set_title(f"{neuron} {plot_label} Response to Drop")
        ax.legend()
        ax.grid(True)

        save_path = os.path.join(self.output_dir, self.dataname, f"{plot_label}.png")
        plt.savefig(save_path, dpi=300)
        plt.close()



# data = [data/'08202024_Intact_Cold.csv', 'data/08292022_Female_Intact_Cold.csv', 'data/12172014_BAK_Day14_RatIV_Cold.csv', 'data/12192024_Bak_Day14_RatIII_Cold.csv']

# data = [ 'data/12192024_Bak_Day14_RatIII_Cold.csv']

# for dataset in data:

#     data_name = os.path.basename(dataset) 

#     out_folder = 'data_out'
#     user_confirmation=True
#     plot_orig=True
#     plot_after=True

#     force_basal_computation=True
#     temp_col = 'Temp'
#     time_col = 'Time'
#     window_before = 30
#     window_after = 30
#     std_threshold = 2
#     save_plots = True

#     data = pd.read_csv(dataset)
#     print(data_name)
#     # path = 'data/'+dataset
#     tool = TimeFinder(data, dataname = data_name, output_dir=out_folder, file_path=dataset)
#     results = tool.run_analysis(plot_orig=plot_orig,user_confirmation=user_confirmation, plot_after=plot_after)
#     print(results['drop_times'])
#     # Initialize DropAnalysis 
#     analysis = DropAnalysis(data, 
#                             results["drop_times"], 
#                             results["recovery_times"], 
#                             output_dir= out_folder, 
#                             force_basal_computation=force_basal_computation,
#                             temp_col = temp_col,
#                             time_col = time_col,
#                             window_before=window_before,
#                             window_after=window_after,
#                             std_threshold=std_threshold,
#                             save_plots = save_plots,
#                             dataname=data_name,
#                             )
    
#     analysis.analyze_drops()







# Run visualization
# plot_stim_periods(pd.read_csv(data[0]), drop_times, recovery_times)
