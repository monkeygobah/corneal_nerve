import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
import threading
from time_finder import TimeFinder
from drop_analysis import DropAnalysis  

class DropAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Drop Analysis Tool")

        # **File Selection**
        tk.Label(root, text="Select CSV File:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.file_entry = tk.Entry(root, width=50, state="disabled")
        self.file_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Button(root, text="Browse", command=self.load_file).grid(row=0, column=2, padx=5, pady=2)

        # **Output Folder**
        tk.Label(root, text="Output Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.out_folder_entry = tk.Entry(root, width=30)
        self.out_folder_entry.insert(0, "data_out")
        self.out_folder_entry.grid(row=1, column=1, padx=5, pady=2)

        # **User Confirmation & Plotting Options**
        self.user_confirmation_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Enable User Confirmation", variable=self.user_confirmation_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.plot_orig_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Plot Original Data", variable=self.plot_orig_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.plot_after_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Plot After Analysis", variable=self.plot_after_var).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        self.save_plots_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Save Plots", variable=self.save_plots_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # **Force Basal Computation**
        self.force_basal_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Force Basal Computation", variable=self.force_basal_var).grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # **Parameters: Time, Temperature, Windows**
        self.create_param_input("Time Column:", "Time", 7)
        self.create_param_input("Temp Column:", "Temp", 8)
        self.create_param_input("Window Before (s):", "30", 9)
        self.create_param_input("Window After (s):", "30", 10)
        self.create_param_input("STD Threshold:", "2", 11)

        # **Run Button**
        self.run_button = tk.Button(root, text="Run Analysis", command=self.run_analysis)
        self.run_button.grid(row=12, column=0, columnspan=3, pady=10)

        # **Status Message**
        self.status_label = tk.Label(root, text="", fg="blue")
        self.status_label.grid(row=13, column=0, columnspan=3, pady=5)

        self.file_path = None  # Store selected file path

    def create_param_input(self, label, default_value, row):
        """Create input fields for user-configurable parameters."""
        tk.Label(self.root, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        entry = tk.Entry(self.root, width=10)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, padx=5, pady=2)
        setattr(self, f"param_{row}", entry)  # Store entry widget dynamically

    def load_file(self):
        """Open file dialog to select a CSV file."""
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.file_path = file_path
            self.file_entry.config(state="normal")
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, os.path.basename(file_path))
            self.file_entry.config(state="disabled")

    def run_analysis(self):
        """Run TimeFinder and DropAnalysis on the selected file."""
        if not self.file_path:
            messagebox.showerror("Error", "Please select a CSV file first!")
            return

        self.status_label.config(text="Running analysis...", fg="black")
        self.root.update_idletasks()

        # Run in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.process_analysis)
        thread.start()

    def process_analysis(self):
        try:
            # **Extract User Inputs**
            data = pd.read_csv(self.file_path)
            dataname = os.path.basename(self.file_path)
            output_dir = self.out_folder_entry.get()
            force_basal_computation = self.force_basal_var.get()
            plot_orig = self.plot_orig_var.get()
            plot_after = self.plot_after_var.get()
            save_plots = self.save_plots_var.get()
            user_confirmation = self.user_confirmation_var.get()

            time_col = self.param_7.get()
            temp_col = self.param_8.get()
            window_before = int(self.param_9.get())
            window_after = int(self.param_10.get())
            std_threshold = float(self.param_11.get())

            # **Run TimeFinder**
            tool = TimeFinder(
                data,
                dataname=dataname,
                output_dir=output_dir,
                file_path=self.file_path
            )
            results = tool.run_analysis(
                plot_orig=plot_orig,
                user_confirmation=user_confirmation,
                plot_after=plot_after
            )

            # **Run DropAnalysis**
            analysis = DropAnalysis(
                df=data,
                drop_times=results["drop_times"],
                recovery_times=results["recovery_times"],
                dataname=dataname,
                time_col=time_col,
                temp_col=temp_col,
                window_before=window_before,
                window_after=window_after,
                std_threshold=std_threshold,
                save_plots=save_plots,
                output_dir=output_dir,
                force_basal_computation=force_basal_computation
            )
            analysis.analyze_drops()

            self.status_label.config(text="Analysis completed successfully!", fg="green")
            messagebox.showinfo("Success", "Analysis completed successfully!")

        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg="red")
            messagebox.showerror("Error", f"Analysis failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = DropAnalysisGUI(root)
    root.mainloop()
