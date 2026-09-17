#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Hunter
Institutional Cluster Submission Script Generator
================================================

Purpose:
--------
Interactive generator for Hunter submission scripts in the research group's
configured Capitán (CCT-Rosario) and Serafín (CCAD-UNC) environments. It preserves
the institutional resource policies, environment setup and submission workflow.
This helper does not provide universal HPC or SLURM support.

Author:
-------
DGDTL Research Team
Prof. José A. Pérez (JP)

Version:
--------
1.0.0 (institutional multi-cluster edition)

Copyright:
----------
Copyright (c) 2026 José A. Pérez.

License:
--------
MIT License. See the LICENSE file distributed with this software.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Terminal colour helpers
# ---------------------------------------------------------------------------

class C:
    HEADER = '\033[95m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'
    BOLD   = '\033[1m'


# ---------------------------------------------------------------------------
# Cluster-level constants
# ---------------------------------------------------------------------------

# Capitán — contributing group partitions
CAPITAN_GROUPS = [
    'colisiones', 'colisionesNuevo', 'matcond', 'ferro',
    'sistint', 'fiquin', 'iicar', 'organica', 'sintesis',
]

ORGANICA_EXCLUDED_NODES = "compute-10-9,compute-10-10"
CAPITAN_DISABLED = {'eth_hi', 'eth_low'}
SERAFIN_CPUS = 64


# ---------------------------------------------------------------------------
# Cluster selection
# ---------------------------------------------------------------------------

def select_cluster() -> str:
    menu = (
        f"\n{C.CYAN}{C.BOLD}{'='*62}\n"
        f"   DGDTL JOB SCRIPT GENERATOR — UNIFIED MULTI-CLUSTER EDITION\n"
        f"   1.0.0 — Reproducibility-safe partition policy\n"
        f"{'='*62}{C.ENDC}\n\n"
        f"{C.HEADER}--- TARGET CLUSTER SELECTION ---{C.ENDC}\n"
        f"{C.YELLOW}"
        f"  [1] Capitan  — CCT-Rosario, CONICET  (output: .sh)\n"
        f"  [2] Serafin  — CCAD, UNC Cordoba     (output: .sge, 64 cores fixed)\n"
        f"Selection: {C.ENDC}"
    )
    choice = input(menu).strip()
    while choice not in ('1', '2'):
        print(f"{C.RED}Invalid input. Please enter 1 or 2.{C.ENDC}")
        choice = input(f"{C.YELLOW}Selection: {C.ENDC}").strip()
    return 'capitan' if choice == '1' else 'serafin'


# ---------------------------------------------------------------------------
# Cluster configuration — Capitán
# ---------------------------------------------------------------------------

class CapitanConfig:
    REPRO_NOTES = {
        'ib100': (
            "# Reproducibility: GROUP A — bit-identical to reference laptop.\n"
            "# Hardware: AMD EPYC 7513 (compute-3-[0-4]). Verified nit=49 (2026-04-26).\n"
        ),
        'organica': (
            "# Reproducibility: GROUP B — internally consistent across organica nodes.\n"
            f"# Excluded nodes: {ORGANICA_EXCLUDED_NODES} (Xeon Gold 5318Y, Group C, nit=41/81).\n"
            "# NOTE: Results differ from Group A (laptop/ib100/Serafin).\n"
            "# Use ib100 or Serafin when cross-cluster reproducibility is required.\n"
        ),
    }

    def __init__(self):
        self.partition      = ""
        self.account        = ""
        self.nodes          = "1"
        self.ntasks         = "1"
        self.ntasks_per_node = ""
        self.cpus           = "16"
        self.time           = "24:00:00"
        self.env_name       = "dgdtl_v2"
        self.gpu_gres       = ""
        self.exclude_nodes  = ""
        self.exec_prefix    = ""  # No srun needed by default for basic python scripts

    def configure(self):
        print(f"\n{C.HEADER}--- CAPITAN: QUEUE SELECTION ---{C.ENDC}")

        part_map = {
            '1': 'organica',
            '2': 'ib100',
            '3': 'eth_epyc',
            '4': 'gpua10_hi',
            '5': 'gpua10_low',
            '6': '__group__',
            '7': '__disabled__',
        }

        menu = (
            f"{C.YELLOW}"
            f"  [1] organica    — Group B: i7/Ryzen nodes (nit=25).\n"
            f"                    Xeon Gold nodes auto-excluded. --account set automatically.\n"
            f"  [2] ib100       — Group A: EPYC 7513 (nit=49). Bit-identical to laptop.\n"
            f"                    Requires >=2 nodes. Restricted access. Max 48h.\n"
            f"  [3] eth_epyc    — Group A (probable). Verify before use.\n"
            f"  [4] gpua10_hi   — GPU nodes, compute-2. Max 48h.\n"
            f"  [5] gpua10_low  — GPU nodes, compute-2. Preemptible. Max 48h.\n"
            f"  [6] group       — Contributing group partition (organica, matcond, etc.).\n"
            f"  [7] eth_hi/low  — {C.RED}DISABLED{C.YELLOW}"
            f" — Opteron 6282 SE, no AVX2 (Group D).\n"
            f"Selection: {C.ENDC}"
        )
        choice = input(menu).strip()
        while choice not in part_map:
            print(f"{C.RED}Invalid input.{C.ENDC}")
            choice = input(f"{C.YELLOW}Selection: {C.ENDC}").strip()

        target = part_map[choice]
        if target == '__group__':
            self._configure_group_partition()
        elif target == '__disabled__':
            self._handle_disabled()
        else:
            self.partition = target

        if self.partition == 'organica':
            self.exclude_nodes = ORGANICA_EXCLUDED_NODES
            self.account = 'organica'
            print(
                f"{C.GREEN}"
                f"  → --account=organica assigned automatically.\n"
                f"  → --exclude={ORGANICA_EXCLUDED_NODES} assigned automatically.\n"
                f"     (Xeon Gold 5318Y, Group C — incompatible SLSQP trajectories)\n"
                f"{C.ENDC}"
            )

        if self.partition == 'ib100':
            self.nodes = '2'
            self.ntasks = input(
                f"{C.YELLOW}Total MPI tasks for ib100 "
                f"(must be a multiple of 2; default 8): {C.ENDC}"
            ).strip() or '8'
            try:
                self.ntasks_per_node = str(int(self.ntasks) // int(self.nodes))
            except ValueError:
                self.ntasks_per_node = '4'
            print(
                f"{C.GREEN}"
                f"  → --nodes=2  --ntasks={self.ntasks}  "
                f"--ntasks-per-node={self.ntasks_per_node}\n"
                f"  → ib100: Group A confirmed (EPYC 7513, nit=49).\n"
                f"{C.ENDC}"
            )

        if 'gpua10' in self.partition:
            req = input(
                f"{C.YELLOW}Request GPUs for this job? [y/n] (default: y): {C.ENDC}"
            ).strip().lower()
            if req != 'n':
                n_gpu = input(
                    f"{C.YELLOW}Number of GPUs (default: 1): {C.ENDC}"
                ).strip() or '1'
                self.gpu_gres = f"gpu:{n_gpu}"

        self.cpus = input(
            f"{C.YELLOW}CPUs per task (--cpus-per-task, recommended 16): {C.ENDC}"
        ).strip() or '16'

        self._configure_time({'1': '12:00:00', '5': '24:00:00',
                               '9': '28:00:00', '0': '48:00:00'})

        self.env_name = input(
            f"{C.YELLOW}Conda environment name (default: dgdtl_v2): {C.ENDC}"
        ).strip() or 'dgdtl_v2'

    def _configure_group_partition(self):
        menu = f"{C.YELLOW}Select contributing group:\n"
        for i, g in enumerate(CAPITAN_GROUPS, start=1):
            note = f"  {C.GREEN}(Group B — Xeon Gold auto-excluded){C.YELLOW}" \
                   if g == 'organica' else ""
            menu += f"  [{i}] {g}{note}\n"
        menu += f"Selection: {C.ENDC}"

        valid = {str(i): g for i, g in enumerate(CAPITAN_GROUPS, start=1)}
        choice = input(menu).strip()
        while choice not in valid:
            print(f"{C.RED}Invalid input.{C.ENDC}")
            choice = input(f"{C.YELLOW}Selection: {C.ENDC}").strip()

        self.partition = valid[choice]
        self.account   = valid[choice]

        if self.partition == 'organica':
            self.exclude_nodes = ORGANICA_EXCLUDED_NODES
            print(
                f"{C.GREEN}"
                f"  → --partition=organica  --account=organica\n"
                f"  → --exclude={ORGANICA_EXCLUDED_NODES} assigned automatically.\n"
                f"{C.ENDC}"
            )
        else:
            print(
                f"{C.GREEN}"
                f"  → --partition={self.partition}  --account={self.account}\n"
                f"{C.ENDC}"
            )

    def _handle_disabled(self):
        print(
            f"\n{C.RED}{C.BOLD}DISABLED PARTITION{C.ENDC}\n"
            f"{C.RED}"
            f"  eth_hi and eth_low exclusively contain AMD Opteron 6282 SE nodes\n"
            f"  (Bulldozer, 2011, no AVX2 — Group D). SLSQP produces non-reproducible\n"
            f"  results on this hardware. These partitions are permanently disabled\n"
            f"  for DGDTL jobs.\n\n"
            f"  Recommended alternatives:\n"
            f"    [1] organica — Group B, internally consistent.\n"
            f"    [2] ib100    — Group A, bit-identical to laptop.\n"
            f"    [Serafin]    — Group A, bit-identical to laptop.\n"
            f"{C.ENDC}"
        )
        self.configure()

    def _configure_time(self, time_map: dict):
        opts = '  '.join(f"[{k}] {v}" for k, v in time_map.items())
        choice = input(
            f"{C.YELLOW}Walltime — {opts}: {C.ENDC}"
        ).strip()
        while choice not in time_map:
            print(f"{C.RED}Invalid input.{C.ENDC}")
            choice = input(f"{C.YELLOW}Walltime: {C.ENDC}").strip()
        self.time = time_map[choice]

    def repro_note(self) -> str:
        return self.REPRO_NOTES.get(
            self.partition,
            f"# Reproducibility: partition '{self.partition}' — verify hardware group.\n"
        )

    def build_sbatch_header(self, job_name: str) -> list:
        lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name={job_name}",
            f"#SBATCH --nodes={self.nodes}",
            f"#SBATCH --partition={self.partition}",
        ]
        if self.account:
            lines.append(f"#SBATCH --account={self.account}")
        if self.ntasks_per_node:
            lines.append(f"#SBATCH --ntasks={self.ntasks}")
            lines.append(f"#SBATCH --ntasks-per-node={self.ntasks_per_node}")
        else:
            lines.append("#SBATCH --ntasks=1")
        lines.append(f"#SBATCH --cpus-per-task={self.cpus}")
        if self.exclude_nodes:
            lines.append(f"#SBATCH --exclude={self.exclude_nodes}")
        if self.gpu_gres:
            lines.append(f"#SBATCH --gres={self.gpu_gres}")
        lines += [
            f"#SBATCH --time={self.time}",
            f"#SBATCH --output={job_name}_%j.log",
            f"#SBATCH --error={job_name}_%j.err",
        ]
        return lines

    def build_env_section(self) -> str:
        return (
            "# -------- SECTION: VIRTUAL ENVIRONMENT (MINIFORGE3) -------------\n"
            'echo ">> Initialising Miniforge3..."\n'
            'eval "$(/home/$USER/miniforge3/bin/conda shell.bash hook)"\n'
            f'echo ">> Activating environment: {self.env_name}..."\n'
            f'conda activate {self.env_name}\n'
            'PYTHON_EXE=$(which python)\n'
            'echo ">> Python executable: $PYTHON_EXE"\n'
            'echo " "\n'
        )

    def build_scratch_section(self) -> str:
        return (
            "# -------- SECTION: LOCAL SCRATCH (CLUSTER POLICY) ---------------\n"
            'echo ">> Configuring temporary directory (Scratch)..."\n'
            'if [ ! -d "/local/$USER" ]; then\n'
            '    mkdir -p /local/$USER\n'
            'fi\n'
            'DGDTL_SCRDIR=/local/$USER/$SLURM_JOB_ID\n'
            'export DGDTL_SCRDIR\n'
            'export TMPDIR=$DGDTL_SCRDIR\n'
            'if [[ ! -d "$DGDTL_SCRDIR" ]]; then\n'
            '    mkdir -p "$DGDTL_SCRDIR"\n'
            'fi\n'
            'echo ">> Scratch created at: $DGDTL_SCRDIR"\n'
            'echo " "\n'
        )

    def build_cleanup_section(self) -> str:
        return (
            '# -------- SECTION: CLEANUP & STATISTICS -------------------------\n'
            'echo " "\n'
            'echo ">> Cleaning up temporary directory (Scratch)..."\n'
            'rm -rf $DGDTL_SCRDIR\n'
            'echo ">> Cleanup completed."\n'
            'echo " "\n'
            '# -------- MANDATORY ACKNOWLEDGMENTS (CAPITAN POLICY) ------------\n'
            'echo "==============================================================="\n'
            'echo "AGRADECIMIENTOS / ACKNOWLEDGMENTS"\n'
            # English translation; preserve the institutional Spanish text below.
            'echo "[Part of] The results presented in this work were obtained using"\n'
            'echo "the resources of the Centro de Cómputos de CCT-Rosario, a member"\n'
            'echo "of the Sistema Nacional de Computación de Alto Desempeño"\n'
            'echo "(SNCAD, MincyT- Argentina)."\n'
            'echo " "\n'
            'echo "[Parte de] Los resultados presentes en este trabajo fueron"\n'
            'echo "obtenidos utilizando los recursos del Centro de Cómputos de"\n'
            'echo "CCT-Rosario, miembro del Sistema Nacional de Computación de"\n'
            'echo "Alto Desempeño (SNCAD, MincyT- Argentina)."\n'
            'echo "==============================================================="\n'
            'echo " "\n'
        )


# ---------------------------------------------------------------------------
# Cluster configuration — Serafín
# ---------------------------------------------------------------------------

class SerafinConfig:
    REPRO_NOTE = (
        "# Reproducibility: GROUP A — bit-identical to reference laptop.\n"
        "# Hardware: AMD EPYC 7532 (Zen2). Verified nit=49 (2026-04-26).\n"
        f"# Fixed allocation: {SERAFIN_CPUS} CPUs per task (site policy: full node).\n"
    )

    PARTITION_MAP = {
        '1': ('short', '0-01:00:00'),  # max 1h (Format: days-hours:minutes:seconds)
        '2': ('multi', '2-00:00:00'),  # max 48h
    }

    def __init__(self):
        self.partition = ""
        self.cpus      = str(SERAFIN_CPUS)   # Fixed — site policy
        self.time      = ""
        self.env_name  = "dgdtl_v2"
        self.exec_prefix = "srun "  # Serafin dictates srun execution

    def configure(self):
        print(f"\n{C.HEADER}--- SERAFIN: QUEUE SELECTION ---{C.ENDC}")
        print(
            f"{C.GREEN}"
            f"  Note: --cpus-per-task={SERAFIN_CPUS} is fixed by site policy\n"
            f"  (full node: 2 × AMD EPYC 7532 × 32 cores).\n"
            f"  Group A confirmed: bit-identical to reference laptop (nit=49).\n"
            f"{C.ENDC}"
        )

        menu = (
            f"{C.YELLOW}"
            f"  [1] short  — Max 1h.  Suitable for testing and short production runs.\n"
            f"  [2] multi  — Max 48h. Suitable for full DGDTL Hunter production runs.\n"
            f"Selection: {C.ENDC}"
        )
        choice = input(menu).strip()
        while choice not in self.PARTITION_MAP:
            print(f"{C.RED}Invalid input.{C.ENDC}")
            choice = input(f"{C.YELLOW}Selection: {C.ENDC}").strip()
        
        self.partition, self.time = self.PARTITION_MAP[choice]

        self.env_name = input(
            f"{C.YELLOW}Conda environment name (default: dgdtl_v2): {C.ENDC}"
        ).strip() or 'dgdtl_v2'

    def repro_note(self) -> str:
        return self.REPRO_NOTE

    def build_sbatch_header(self, job_name: str) -> list:
        return [
            "#!/bin/bash",
            f"#SBATCH --job-name={job_name}",
            f"#SBATCH --nodes=1", # Explicit 1 node based on doc
            f"#SBATCH --ntasks=1",
            f"#SBATCH --cpus-per-task={self.cpus}",
            f"#SBATCH --partition={self.partition}",
            f"#SBATCH --time={self.time}",
            f"#SBATCH --output={job_name}_%j.log",
            f"#SBATCH --error={job_name}_%j.err",
        ]

    def build_env_section(self) -> str:
        return (
            "# -------- SECTION: VIRTUAL ENVIRONMENT (SERAFIN) ---------------\n"
            'echo ">> Loading system profiles (Serafin policy)..."\n'
            '. /etc/profile\n'
            'echo ">> Initialising Miniforge3..."\n'
            'eval "$(/home/$USER/miniforge3/bin/conda shell.bash hook)"\n'
            f'echo ">> Activating environment: {self.env_name}..."\n'
            f'conda activate {self.env_name}\n'
            'PYTHON_EXE=$(which python)\n'
            'echo ">> Python executable: $PYTHON_EXE"\n'
            'export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK\n'
            'echo " "\n'
        )

    def build_scratch_section(self) -> str:
        return (
            "# -------- SECTION: LOCAL SCRATCH (CLUSTER POLICY) ---------------\n"
            'echo ">> Configuring temporary directory (Scratch)..."\n'
            'DGDTL_SCRDIR=/tmp/$SLURM_JOB_ID\n'
            'export DGDTL_SCRDIR\n'
            'export TMPDIR=$DGDTL_SCRDIR\n'
            'mkdir -p "$DGDTL_SCRDIR"\n'
            'echo ">> Scratch created at: $DGDTL_SCRDIR"\n'
            'echo " "\n'
        )

    def build_cleanup_section(self) -> str:
        return (
            '# -------- SECTION: CLEANUP & STATISTICS -------------------------\n'
            'echo " "\n'
            'echo ">> Cleaning up temporary directory (Scratch)..."\n'
            'rm -rf $DGDTL_SCRDIR\n'
            'echo ">> Cleanup completed."\n'
            # Approved standalone adaptation of scripts/source/paper_dgdtl.pdf,
            # ACKNOWLEDGMENTS, p. 12434; DOI: 10.1021/acs.jcim.5c02048.
            'echo " "\n'
            '# -------- ACKNOWLEDGMENTS (SERAFIN / CCAD) -----------------------\n'
            'echo "==============================================================="\n'
            'echo "ACKNOWLEDGMENTS"\n'
            'echo "This work used computational resources from UNC Supercómputo (CCAD) –"\n'
            'echo "Universidad Nacional de Córdoba, which are part of SNCAD,"\n'
            'echo "República Argentina."\n'
            'echo "==============================================================="\n'
            'echo " "\n'
        )


# ---------------------------------------------------------------------------
# DGDTL Hunter model configuration (cluster-independent)
# ---------------------------------------------------------------------------

class HunterConfig:
    def __init__(self):
        self.job_name    = "dgdtl_job"
        self.train_file  = "data_train.csv"
        self.valid_file  = "data_valid.csv"
        self.out_dir     = ""
        self.mode        = "raw"
        self.use_intercept = True
        self.beta_sum_one  = False
        self.norm_x      = True
        self.norm_y      = False
        self.formulas    = ""

    def configure(self):
        print(f"\n{C.HEADER}--- DGDTL MODEL CONFIGURATION ---{C.ENDC}")

        self.job_name = input(
            f"{C.YELLOW}Job name (e.g., domain_A): {C.ENDC}"
        ).strip() or "dgdtl_job"

        self.train_file = input(
            f"{C.YELLOW}Training file name (default: data_train.csv): {C.ENDC}"
        ).strip() or "data_train.csv"

        self.valid_file = input(
            f"{C.YELLOW}Validation file name (default: data_valid.csv): {C.ENDC}"
        ).strip() or "data_valid.csv"

        self.out_dir = input(
            f"{C.YELLOW}Output directory name (default: results_{self.job_name}): {C.ENDC}"
        ).strip() or f"results_{self.job_name}"

        mode_in = input(
            f"{C.YELLOW}Model mode [raw / error_matrix] (default: raw): {C.ENDC}"
        ).strip().lower()
        self.mode = mode_in if mode_in in ('raw', 'error_matrix') else 'raw'

        self.use_intercept = input(
            f"{C.YELLOW}Fit intercept? [y/n] (default: y): {C.ENDC}"
        ).strip().lower() != 'n'

        self.beta_sum_one = input(
            f"{C.YELLOW}Constrain betas to sum = 1? [y/n] (default: n): {C.ENDC}"
        ).strip().lower() == 'y'

        self.norm_x = input(
            f"{C.YELLOW}Normalize predictors X? [y/n] (default: y): {C.ENDC}"
        ).strip().lower() != 'n'

        if self.mode == 'raw':
            self.norm_y = input(
                f"{C.YELLOW}Normalize target Y? [y/n] (default: n): {C.ENDC}"
            ).strip().lower() == 'y'

        self.formulas = input(
            f"{C.YELLOW}Feature engineering formulas, space-separated "
            f"(e.g., 'A*B' 'C**2'), or press Enter to skip: {C.ENDC}"
        ).strip()

    def build_command(self, exec_prefix: str = "") -> str:
        cmd  = f"{exec_prefix}python dgdtl_hunter_umaxp_cluster.py \\\n"
        cmd += f'    --train "{self.train_file}" \\\n'
        cmd += f'    --valid "{self.valid_file}" \\\n'
        cmd += f'    --out-dir "{self.out_dir}" \\\n'
        cmd += f"    --mode {self.mode}"
        if not self.use_intercept:
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


# ---------------------------------------------------------------------------
# Unified script generator
# ---------------------------------------------------------------------------

class DGDTLJobGenerator:
    def __init__(self):
        self.cluster_id  = ""
        self.cluster_cfg = None
        self.hunter      = HunterConfig()
        self.target_dir  = ""

    def _setup_directory(self):
        print(f"\n{C.HEADER}--- EXPERIMENT LOCATION ---{C.ENDC}")
        print(
            f"{C.YELLOW}"
            f"  Specify the folder containing the data files.\n"
            f"  The submission script will be written to the same location.\n"
            f"  Accepted formats: absolute (/home/user/exp1), relative (../exp1),\n"
            f"  or tilde-expanded (~/exp1). Press Enter to use the current directory.\n"
            f"{C.ENDC}"
        )
        dir_input = input(f"{C.CYAN}Path: {C.ENDC}").strip(" '\"\n\r")
        self.target_dir = (
            os.path.abspath(os.path.expanduser(dir_input))
            if dir_input else os.getcwd()
        )
        if not os.path.exists(self.target_dir):
            sys.exit(
                f"{C.RED}Error: path '{self.target_dir}' does not exist. "
                f"Exiting.{C.ENDC}"
            )
        os.chdir(self.target_dir)
        print(f"{C.GREEN}  Target directory: {self.target_dir}{C.ENDC}\n")

    def run(self):
        self.cluster_id  = select_cluster()
        self.cluster_cfg = (
            CapitanConfig() if self.cluster_id == 'capitan' else SerafinConfig()
        )
        self._setup_directory()
        self.cluster_cfg.configure()
        self.hunter.configure()
        self._write_script()

    def _build_repro_check(self) -> str:
        return (
            "# -------- SECTION: REPRODUCIBILITY CHECK AT RUNTIME ------------\n"
            'CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs)\n'
            'echo ">> CPU model: $CPU_MODEL"\n'
            'if grep -q "avx2" /proc/cpuinfo; then\n'
            '    echo ">> AVX2: PRESENT — node is compatible with DGDTL reproducibility."\n'
            'else\n'
            '    echo ">> AVX2: NOT FOUND — WARNING: possible Group D node (Opteron 6282)."\n'
            'fi\n'
            'echo " "\n'
        )

    def _build_timing_footer(self) -> str:
        return (
            'echo "==============================================================="\n'
            'END_TIME=`date +%s`\n'
            'RUN_TIME=$((END_TIME - START_TIME))\n'
            'HOURS=$(echo "scale=4; $RUN_TIME / 3600" | bc)\n'
            'echo "END_TIME (success)   = `date +\'%y-%m-%d %H:%M:%S\'`"\n'
            'echo "RUN_TIME (total)     = $HOURS hours"\n'
            'echo "==============================================================="\n'
        )

    def _write_script(self):
        cfg     = self.cluster_cfg
        hunter  = self.hunter
        ext     = '.sge' if self.cluster_id == 'serafin' else '.sh'
        fname   = f"run_{hunter.job_name}{ext}"
        cluster_label = 'Serafin (CCAD-UNC)' if self.cluster_id == 'serafin' \
                        else 'Capitan (CCT-Rosario)'

        lines = cfg.build_sbatch_header(hunter.job_name)
        lines += [
            "",
            cfg.repro_note(),
            "# -------- SECTION: STARTUP INFO ---------------------------------",
            'echo " "',
            "echo \"START_TIME           = `date +'%y-%m-%d %H:%M:%S'`\"",
            "START_TIME=`date +%s`",
            'echo "HOSTNAME             = $HOSTNAME"',
            'echo "JOB_NAME             = $SLURM_JOB_NAME"',
            'echo "JOB_ID               = $SLURM_JOB_ID"',
            f'echo "CLUSTER              = {cluster_label}"',
            f'echo "WORKING_DIR          = {self.target_dir}"',
            'echo "CPUS                 = $SLURM_CPUS_PER_TASK"',
            'echo " "',
            "",
            self._build_repro_check(),
            cfg.build_scratch_section(),
            cfg.build_env_section(),
            "# -------- SECTION: PROGRAM EXECUTION ----------------------------",
            'echo ">> Executing DGDTL Hunter..."',
            'echo " "',
            "",
            hunter.build_command(cfg.exec_prefix),
            "",
            cfg.build_cleanup_section(),
            "",
            self._build_timing_footer(),
            "",
            "exit 0",
        ]

        final = "\n".join(lines) + "\n"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(final)

        print(
            f"\n{C.GREEN}{C.BOLD}[SUCCESS] {fname} written to:{C.ENDC}\n"
            f"{C.CYAN}{self.target_dir}{C.ENDC}\n"
            f"\n{C.YELLOW}To submit the job, run:{C.ENDC}\n"
            f"  cd {self.target_dir}\n"
            f"  sbatch {fname}\n"
        )


if __name__ == "__main__":
    try:
        DGDTLJobGenerator().run()
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}Interrupted by user.{C.ENDC}")
        sys.exit(0)
    except Exception:
        print(f"\n{C.RED}A critical error occurred:{C.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
