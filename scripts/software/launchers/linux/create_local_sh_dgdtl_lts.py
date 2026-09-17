#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Hunter
Linux Local Batch Script Generator
=================================

Purpose:
--------
Interactive generator for local Hunter execution scripts (.sh). It collects
Hunter configuration and writes a batch script in the selected working
directory. Generated scripts use the active Conda environment.

Author:
-------
DGDTL Research Team
Prof. José A. Pérez (JP)

Version:
--------
1.0.0 (Linux local)

Copyright:
----------
Copyright (c) 2026 José A. Pérez.

License:
--------
MIT License. See the LICENSE file distributed with this software.
"""

import os
import sys

class ConsoleColors:
    """Provides ANSI escape codes for terminal output formatting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class HunterConfig:
    """Encapsulates DGDTL hyperparameter configuration and CLI argument construction."""
    
    def __init__(self):
        self.job_name = "dgdtl_local"
        self.train_file = "data_train.csv"
        self.valid_file = "data_valid.csv"
        self.out_dir = ""
        self.mode = "raw"
        self.fit_intercept = True
        self.beta_sum_one = False
        self.norm_x = True
        self.norm_y = False
        self.formulas = ""

    def configure_interactively(self):
        """Prompts the user to define the execution parameters."""
        print(f"\n{ConsoleColors.HEADER}--- DGDTL MODEL CONFIGURATION (LOCAL EXECUTION) ---{ConsoleColors.ENDC}")
        
        self.job_name = input(
            f"{ConsoleColors.YELLOW}Job name (e.g., domain_A): {ConsoleColors.ENDC}"
        ).strip() or "dgdtl_local"
        
        self.train_file = input(
            f"{ConsoleColors.YELLOW}Training dataset filename (Default: data_train.csv): {ConsoleColors.ENDC}"
        ).strip() or "data_train.csv"
        
        self.valid_file = input(
            f"{ConsoleColors.YELLOW}Validation dataset filename (Default: data_valid.csv): {ConsoleColors.ENDC}"
        ).strip() or "data_valid.csv"
        
        self.out_dir = input(
            f"{ConsoleColors.YELLOW}Output directory (Default: results_{self.job_name}): {ConsoleColors.ENDC}"
        ).strip() or f"results_{self.job_name}"

        mode_input = input(
            f"{ConsoleColors.YELLOW}Optimization mode [raw / error_matrix] (Default: raw): {ConsoleColors.ENDC}"
        ).strip().lower()
        self.mode = 'error_matrix' if mode_input == 'error_matrix' else 'raw'

        intercept_input = input(
            f"{ConsoleColors.YELLOW}Fit intercept? [y/n] (Default: y): {ConsoleColors.ENDC}"
        ).strip().lower()
        self.fit_intercept = False if intercept_input == 'n' else True

        beta_sum_input = input(
            f"{ConsoleColors.YELLOW}Constrain beta coefficients to sum to 1? [y/n] (Default: n): {ConsoleColors.ENDC}"
        ).strip().lower()
        self.beta_sum_one = True if beta_sum_input == 'y' else False

        norm_x_input = input(
            f"{ConsoleColors.YELLOW}Normalize predictors (X-matrix)? [y/n] (Default: y): {ConsoleColors.ENDC}"
        ).strip().lower()
        self.norm_x = False if norm_x_input == 'n' else True

        if self.mode == 'raw':
            norm_y_input = input(
                f"{ConsoleColors.YELLOW}Normalize target (Y-vector)? [y/n] (Default: n): {ConsoleColors.ENDC}"
            ).strip().lower()
            self.norm_y = True if norm_y_input == 'y' else False

        self.formulas = input(
            f"{ConsoleColors.YELLOW}Additional feature engineering formulas separated by space\n"
            f"(e.g., 'A*B' 'C**2', or press Enter to skip): {ConsoleColors.ENDC}"
        ).strip()

    def build_command(self) -> str:
        """Constructs the structured bash command for the Python execution."""
        cmd  = "python dgdtl_hunter_umaxp_cluster.py \\\n"
        cmd += f'    --train "{self.train_file}" \\\n'
        cmd += f'    --valid "{self.valid_file}" \\\n'
        cmd += f'    --out-dir "{self.out_dir}" \\\n'
        cmd += f"    --mode {self.mode}"

        if not self.fit_intercept:
            cmd += " \\\n    --no-intercept"
        if self.beta_sum_one:
            cmd += " \\\n    --beta-sum-one"
        if not self.norm_x:
            cmd += " \\\n    --no-norm-x"
        if self.norm_y:
            cmd += " \\\n    --norm-y"
        if self.formulas:
            cmd += f" \\\n    --formulas {self.formulas}"

        return cmd


class LocalBatchGenerator:
    """Orchestrates the directory setup and generates the final .sh script."""
    
    def __init__(self):
        self.config = HunterConfig()
        self.target_directory = ""

    def setup_working_directory(self):
        """Requests and validates the target working directory."""
        print(f"{ConsoleColors.CYAN}{ConsoleColors.BOLD}{'='*60}")
        print("   LOCAL BATCH SCRIPT GENERATOR FOR DGDTL HUNTER")
        print(f"{'='*60}{ConsoleColors.ENDC}\n")

        print(f"{ConsoleColors.HEADER}--- WORKING DIRECTORY ---{ConsoleColors.ENDC}")
        dir_input = input(
            f"{ConsoleColors.YELLOW}Provide the target path for data files and the .sh script\n"
            f"(Press Enter to use current directory): {ConsoleColors.ENDC}"
        ).strip(" '\"\n\r")

        if not dir_input:
            self.target_directory = os.getcwd()
        else:
            self.target_directory = os.path.abspath(os.path.expanduser(dir_input))

        if not os.path.exists(self.target_directory):
            sys.exit(
                f"{ConsoleColors.RED}[ERROR] The specified path '{self.target_directory}' "
                f"does not exist. Aborting.{ConsoleColors.ENDC}"
            )

        os.chdir(self.target_directory)
        print(f"{ConsoleColors.GREEN}✓ Working directory set to: {self.target_directory}{ConsoleColors.ENDC}\n")

    def generate_script(self):
        """Compiles the bash script content and writes it to the file system."""
        sh_filename = f"run_{self.config.job_name}.sh"
        execution_command = self.config.build_command()

        script_content = f"""#!/bin/bash
# ====================================================================
# DGDTL HUNTER - LOCAL EXECUTION BATCH SCRIPT
# Auto-generated profile for: {self.config.job_name}
# ====================================================================

echo "=========================================================="
echo " INITIATING LOCAL EXECUTION: {self.config.job_name}"
echo "=========================================================="

# -------- SECTION: REPRODUCIBILITY CONTROLS ---------------------
# These environmental variables ensure deterministic behavior and 
# prevent underlying linear algebra libraries from over-subscribing 
# local CPU cores, matching HPC cluster conditions.
export PYTHONHASHSEED=0
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo ">> Reproducibility and thread-control variables applied."

# -------- SECTION: MODEL EXECUTION ------------------------------
echo ">> Verifying active Python environment..."
PYTHON_EXE=$(which python)
echo ">> Active Python interpreter: $PYTHON_EXE"
echo " "
echo ">> Launching DGDTL Hunter Pipeline..."
echo " "

{execution_command}

echo " "
echo ">> Execution completed. Please review the output directory."
echo "=========================================================="
"""
        # Write the file
        with open(sh_filename, "w", encoding='utf-8') as script_file:
            script_file.write(script_content)
            
        # Automatically grant execution permissions in Unix-like systems (chmod +x)
        os.chmod(sh_filename, 0o755)

        self._print_success_message(sh_filename)

    def _print_success_message(self, filename: str):
        """Displays completion instructions to the user."""
        print(f"\n{ConsoleColors.GREEN}{ConsoleColors.BOLD}[SUCCESS] Script '{filename}' successfully generated and granted execution permissions in:{ConsoleColors.ENDC}")
        print(f"{ConsoleColors.CYAN}{self.target_directory}{ConsoleColors.ENDC}")
        print(f"\n{ConsoleColors.YELLOW}To execute the model, ensure your Conda environment is active and run:{ConsoleColors.ENDC}")
        print(f"cd {self.target_directory}")
        print(f"./{filename}\n")

    def run(self):
        """Main execution sequence."""
        self.setup_working_directory()
        self.config.configure_interactively()
        self.generate_script()


if __name__ == "__main__":
    try:
        generator = LocalBatchGenerator()
        generator.run()
    except KeyboardInterrupt:
        print(f"\n\n{ConsoleColors.YELLOW}Process interrupted by user. Exiting gracefully.{ConsoleColors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{ConsoleColors.RED}A critical error occurred:{ConsoleColors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
