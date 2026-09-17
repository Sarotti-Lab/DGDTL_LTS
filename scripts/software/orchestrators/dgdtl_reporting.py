# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Reporting Module
Framework Configuration & Terminal Presentation Support
========================================================

Abstract:
---------
This module provides formatting helpers and terminal presentation utilities
used by the DGDTL-LTS Hunter orchestrator. It also defines FrameworkConfig
and VerdictCodes registries for framework-level reporting support.

In the current Hunter architecture, the active Structural Selection Protocol
configuration and verdict registries are supplied by
u_maxp_core.ProtocolConfig and u_maxp_core.ProtocolVerdictCodes. This module
is independent of the DGDTL-LTS and U-MaxP motors and does not depend on
Optuna or any optimization library.

Key Architectural Features:
---------------------------
1. Framework Configuration Registry
   Defines the local framework threshold registry available to reporting
   utilities. The active Hunter protocol configuration is supplied by
   u_maxp_core.ProtocolConfig.

2. Verdict Code Registries
   Provides human-readable labels and descriptions for the verdict codes
   emitted by the structural decision phases.

3. Terminal Presentation
   Provides ANSI colour definitions and a centralized terminal logger for
   informational, success, warning, error, section, and title messages.

4. Output Formatting Utilities
   Provides ANSI-cleaning support for converting colour-formatted terminal
   text into plain-text output when required.

5. Decoupled Auxiliary Architecture
   Contains no dependency on dgdtl_core, u_maxp_core, Optuna, or other
   optimization libraries, allowing reporting and configuration support to
   remain separated from optimization and structural-computation logic.

Sections:
---------
1. ANSI Colour Helpers
   - Colors
2. Utility
   - _strip_ansi
3. Framework Constants
   - FrameworkConfig
4. Verdict Code Registries
   - VerdictCodes
5. Terminal Logger
   - TerminalLogger

Usage:
------
Designed as an auxiliary reporting and configuration module for DGDTL-LTS
orchestration. It provides local framework registries, verdict descriptions,
and terminal presentation utilities without executing DGDTL-LTS optimization
or U-MaxP structural calculations.

Author:
-------
DGDTL Research Team
Prof. José A. Pérez (JP)

Copyright:
----------
Copyright (c) 2026 José A. Pérez.

License:
--------
MIT License. See the LICENSE file distributed with this software.
"""

import re
from typing import Dict


# =============================================================================
# 1. ANSI COLOUR HELPERS
# =============================================================================

class Colors:
    """
    ANSI escape codes for terminal output.
    """
    HEADER = '\033[95m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'
    BOLD   = '\033[1m'


# =============================================================================
# 2. UTILITY
# =============================================================================

def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes for clean file output."""
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)


# =============================================================================
# 3. FRAMEWORK CONSTANTS  (local registry)
# =============================================================================

class FrameworkConfig:
    """
    Thresholds and calibrated parameters for the four-phase GCI Structural
    Selection Framework.

    eps_tie calibration
    -------------------
    Inter-scout corpus: geometric mean of Delta_tie=0.35% and Delta_min=6.1%
        eps_tie* = exp((ln 0.35 + ln 6.1) / 2) ~ 1.46% -> rounded to 2%.
    Intra-Siege corpus (8 domains, 68 scouts, 408 trials):
        Delta_tie_intra=1.857%, Delta_min_intra=2.024%, geom.mean=1.94% -> 2%.
    Invariance across both contexts confirms eps_tie as a structural
    property of the U_MAXP metric space, not an arbitrary threshold.
    """
    EPS_F           = 1e-4
    DELTA_REL       = 0.005
    EPS_TIE         = 0.02
    EPS_PSI         = 1e-8
    ICV_STRONG      = 1.0
    ICV_CONDITIONAL = 0.85
    PSI_RANK_MIN    = 0.5
    PSI_RANK_N_MIN  = 5


# =============================================================================
# 4. VERDICT CODE REGISTRIES
# =============================================================================

class VerdictCodes:
    """
    Human-readable labels for all verdict codes emitted by the four
    framework phases. 
    """

    PHASE1: Dict[str, tuple] = {
        'F1.0':    ('TEQ', 'Topological Equivalence'),
        'F1.1':    ('JDC', 'Joint Density Collapse'),
        'F1.2':    ('IRF', 'Inefficient Refinement'),
        'F1.3':    ('GTR', 'Genuine Topological Refinement'),
        'F1.3phi': ('STP', 'Step Tie — phi Defends R1'),
        'F1.4':    ('SDI', 'Spurious Density Increment'),
        'F1.X':    ('SNG', 'Single Run — No Comparison'),
    }

    PHASE2: Dict[str, tuple] = {
        'F2.0':    ('BND', 'Baseline Native Dominance'),
        'F2.1':    ('SPT', 'Spurious Transfer'),
        'F2.2':    ('TRG', 'Topological Regularization'),
        'F2.2-RT': ('TSA', 'Topological Reg. — Scope Advisory'),
        'F2.3':    ('STD', 'Structural Dominance'),
        'F2.4':    ('ISI', 'Incoherent Scalar Improvement'),
    }

    PHASE4: Dict[str, tuple] = {
        'FA.1': ('DAC', 'DOA Complete',
                 'DGDTL dominated BL_RT on both observable metrics'),
        'FA.2': ('DAE', 'DOA Error',
                 'DGDTL lower error than BL_RT; phi gap expected (BL_RT asymmetry)'),
        'FA.3': ('DPO', 'DOA Phi Only',
                 'DGDTL better structural coherence; BL_RT lower error (data advantage)'),
        'FA.4': ('ROS', 'RT Observable Superior',
                 'BL_RT dominated both observable metrics; DGDTL leads in U_MAXP_k only'),
    }


# =============================================================================
# 5. TERMINAL LOGGER
# =============================================================================

class TerminalLogger:
    """
    Colour-aware console logger for DGDTL orchestrators.
    """

    @classmethod
    def info(cls, msg: str, indent: int = 1) -> None:
        print(f"{'  ' * indent}{msg}")

    @classmethod
    def success(cls, msg: str, indent: int = 1) -> None:
        print(f"{'  ' * indent}{Colors.GREEN}{msg}{Colors.ENDC}")

    @classmethod
    def warning(cls, msg: str, indent: int = 1) -> None:
        print(f"{'  ' * indent}{Colors.YELLOW}{msg}{Colors.ENDC}")

    @classmethod
    def error(cls, msg: str, indent: int = 1) -> None:
        print(f"{'  ' * indent}{Colors.RED}{msg}{Colors.ENDC}")

    @classmethod
    def section(cls, title: str) -> None:
        print(f"\n{Colors.BOLD}{'─'*80}\n{title}\n{'─'*80}{Colors.ENDC}")

    @classmethod
    def title(cls, title: str, subtitle: str = '') -> None:
        lines = [title]
        if subtitle:
            lines.append(subtitle)
        print(
            f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}\n"
            + "\n".join(lines)
            + f"\n{'='*80}{Colors.ENDC}"
        )
