# SPDX-FileCopyrightText: 2026 José A. Pérez
# SPDX-License-Identifier: MIT

"""
DGDTL-LTS Scientific Plotting Module
Publication-Quality Visualization & Diagnostic Support
=======================================================

Abstract:
---------
This module provides the centralized scientific visualization architecture
used by DGDTL-LTS workflows. It defines publication-oriented plotting styles,
figure presets, color palettes, mathematical plotting utilities, diagnostic
visualizations, and DGDTL-specific graphical representations.

The module supports standardized generation of performance curves,
cross-validation analysis panels, statistical diagnostic plots, parity plots,
two-dimensional search heatmaps, DGDTL solution-space representations, and
the adaptive-tunnel Goldilocks Donut visualization.

Key Architectural Features:
---------------------------
1. Publication Format Configuration
   Defines standardized figure dimensions, plotting parameters, typography,
   color palettes, layout presets, and terminal color helpers for consistent
   scientific presentation.

2. Plotting Utilities
   Provides reusable numerical and graphical utilities for curve smoothing,
   dynamic axis construction, axis configuration, palette management, and
   plot-spine control.

3. DGDTL Performance Visualization
   Generates performance, stability, component-diagnosis, and
   precision-versus-robustness plots from DGDTL result tables, either
   individually or as integrated analysis panels.

4. Statistical Diagnostic Visualization
   Generates residuals-versus-fitted, normal Q-Q, scale-location, and
   residuals-versus-leverage diagnostics, including Cook's-distance
   reference curves.

5. Predictive & Search-Space Visualization
   Provides parity plots, two-dimensional search heatmaps, and graphical
   representations of DGDTL candidate solution spaces.

6. DGDTL Topological Visualization
   Implements the Goldilocks Donut representation of Run 1 and Run 2
   solution regions, baseline reference, adaptive search boundaries, and
   local champions.

7. Public Functional API
   Exposes function-level wrappers around the plotting classes so external
   orchestration scripts can invoke visualization routines without depending
   directly on the internal class structure.

Sections:
---------
1. Publication Format Presets & Constants
   - FIGURE_SIZES
   - TIGHT_LAYOUT_RECTS
   - PLOT_PARAMS
   - COLORS
   - Colors

2. Plotting Utilities
   - PlotStyleManager
   - PlotMathUtils

3. Plot Generators & Drawers
   - PerformanceCurveGenerator
   - DGDTLComponentDrawer
   - CVAnalysisPanelGenerator
   - IndividualDGDTLPlotGenerator
   - DiagnosticPlotter
   - ParityPlotter
   - HeatmapPlotter
   - SolutionSpacePlotter
   - GoldilocksDonutPlotter

4. Public API
   - Style and axis utilities
   - Performance and stability plots
   - CV analysis panels
   - Statistical diagnostic plots
   - Parity plots
   - Search heatmaps
   - DGDTL solution-space plots
   - Goldilocks Donut plots

Usage:
------
Designed as an auxiliary scientific visualization module for DGDTL-LTS
orchestration and analysis workflows. Plotting functions accept numerical
results and diagnostic data generated externally and produce standardized
graphical outputs without executing DGDTL-LTS optimization or U-MaxP
structural selection.

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

import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import seaborn as sns  
from matplotlib import colors as mcolors, cm, cycler
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
from scipy.interpolate import Akima1DInterpolator, CubicSpline
from typing import List, Dict, Any, Tuple, Union, Optional
import statsmodels.api as sm
import warnings

# --- Configuration ---
warnings.filterwarnings("ignore", "Values in x were outside bounds")
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning) # Hide Matplotlib warnings


# =============================================================================
# 1. PUBLICATION FORMAT PRESETS & CONSTANTS
# =============================================================================

FIGURE_SIZES = {
    'single_col': (3.5, 2.625),
    'double_col': (7.2, 5.4),
    'presentation': (8, 6),
    'diagnostic_panel': (10, 8),
    'parity_plot': (5, 5),
    'heatmap': (9, 7)
}

TIGHT_LAYOUT_RECTS = {
    'default': [0, 0, 1, 0.95],
    'diagnostic_panel': [0, 0.03, 1, 0.94],
    'none': [0, 0, 1, 1],
}

PLOT_PARAMS = {
    'figure.figsize': FIGURE_SIZES['presentation'],
    'figure.titlesize': 12,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8, # Default = 8
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica'],
    'lines.linewidth': 1.0,
    'lines.markersize': 4,
    'axes.edgecolor': 'black',
    'axes.linewidth': 0.8,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.size': 4,
    'ytick.major.size': 4,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'axes.grid': False,
    'grid.linestyle': '--',
    'grid.linewidth': 0.5,
    'grid.alpha': 0.5,
}

blues_palette = [mcolors.to_hex(mcolors.LinearSegmentedColormap.from_list(
    "final_blue_gradient", [(0.0, '#409cff'), (0.4, '#0033a0'), (1.0, '#00103A')]
)(i)) for i in np.linspace(0, 1, 5)]

COLORS = {
    'impact': ['#005f73', '#d62828', '#8338ec', '#f28f3b', '#e71d73'],
    'blues': blues_palette,
    'reds': ['#ffb703', '#f28f3b', '#d62828', '#9d0208', '#6a040f'],
    'greens': ['#99d98c', '#43aa8b', '#1b998b', '#007f5f', '#004b23'],
    'violets': ['#c77dff', '#8338ec', '#5a189a', '#3c096c', '#240046'],
    'grayscale': [mcolors.to_hex(cm.Greys(i)) for i in np.linspace(0.3, 0.9, 5)],
    'cbrewer_safe': ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e'],
    'neutrals': {'fill': '#e9ecef', 'points': '#212529', 'line': '#adb5bd'}
}

COLORS['plot_theme'] = {
    'main_line': COLORS['blues'][2],
    'fill_area': COLORS['blues'][0],
    'accent_line': COLORS['reds'][3],
    'point_marker': COLORS['neutrals']['points']
}

PLOT_PARAMS['axes.prop_cycle'] = cycler(color=COLORS['impact'])


# --- ANSI COLORS FOR TERMINAL UI ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# =============================================================================
# CORE CLASSES - UTILITIES
# =============================================================================

class PlotStyleManager:
    """Manages global plotting styles, palettes, and axes cleanup."""
    
    @staticmethod
    def apply_style() -> None:
        plt.rcParams.update(PLOT_PARAMS)

    @staticmethod
    def set_palette(name: str = 'impact') -> None:
        try:
            PLOT_PARAMS['axes.prop_cycle'] = cycler(color=COLORS[name])
            PlotStyleManager.apply_style()
        except KeyError:
            print(f"Error: Palette '{name}' not found.")

    @staticmethod
    def clean_spines(ax: plt.Axes, left: bool = True, right: bool = True, top: bool = True, bottom: bool = True) -> None:
        ax.spines['top'].set_visible(top)
        ax.spines['right'].set_visible(right)
        ax.spines['left'].set_visible(left)
        ax.spines['bottom'].set_visible(bottom)


class PlotMathUtils:
    """Provides mathematical utilities for smoothing and axis calculations."""
    
    @staticmethod
    def get_smooth_curve(x_raw: Union[pd.Series, np.ndarray, List[float]], y_raw: Union[pd.Series, np.ndarray, List[float]]) -> Tuple[np.ndarray, np.ndarray]:
        x_raw_np = x_raw.to_numpy() if isinstance(x_raw, pd.Series) else np.array(x_raw)
        y_raw_np = y_raw.to_numpy() if isinstance(y_raw, pd.Series) else np.array(y_raw)
        
        valid_mask = ~np.isnan(x_raw_np) & ~np.isnan(y_raw_np)
        x_valid = x_raw_np[valid_mask]
        y_valid = y_raw_np[valid_mask]
        
        sort_idx = np.argsort(x_valid)
        x_sorted = x_valid[sort_idx]
        y_sorted = y_valid[sort_idx]
        
        unique_x, indices = np.unique(x_sorted, return_index=True)
        unique_y = y_sorted[indices]
        
        if len(unique_x) == 0:
            return np.array([]), np.array([])  
        if len(unique_x) == 1:
            return np.array([unique_x[0], unique_x[0]]), np.array([unique_y[0], unique_y[0]])
        if len(unique_x) < 3:
            x_smooth = np.linspace(unique_x[0], unique_x[1], 2)
            y_smooth = np.interp(x_smooth, unique_x, unique_y)
            return x_smooth, y_smooth
        
        try:
            akima = Akima1DInterpolator(unique_x, unique_y)
            x_smooth = np.linspace(unique_x.min(), unique_x.max(), 300)
            return x_smooth, akima(x_smooth)
        except Exception as e:
            print(f"Warning: Akima interpolation failed ({e}). Using linear interpolation.")
            x_smooth = np.linspace(unique_x.min(), unique_x.max(), 300)
            y_smooth = np.interp(x_smooth, unique_x, unique_y)
            return x_smooth, y_smooth

    @staticmethod
    def calculate_dynamic_axis_config(data_series: Union[pd.Series, np.ndarray], target_ticks: int = 9, padding_fraction: float = 0.05) -> Dict[str, Union[List[float], np.ndarray]]:
        if data_series.empty or data_series.isna().all():
            print("[Warning] calculate_dynamic_axis_config received empty data.")
            return {'limits': [0, 1], 'ticks': [0, 0.5, 1]}
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            data_min_raw = np.nanmin(data_series)
            data_max_raw = np.nanmax(data_series)
        
        if not np.isfinite(data_min_raw) or not np.isfinite(data_max_raw):
             print("[Warning] calculate_dynamic_axis_config received non-finite data (inf or -inf).")
             return {'limits': [0, 1], 'ticks': [0, 0.5, 1]}

        data_range = data_max_raw - data_min_raw
        if data_range == 0 or not np.isfinite(data_range):
            padding_range = 0.1 * abs(data_min_raw) if data_min_raw != 0 else 0.1
            padding_range = max(padding_range, 1e-9)
        else:
            padding_range = data_range
        
        padding_amount = padding_range * padding_fraction
        data_min = data_min_raw - padding_amount
        data_max = data_max_raw + padding_amount
        
        if data_min_raw >= 0 and data_min < 0:
            data_min = 0.0
        
        data_range_inflated = data_max - data_min
        if data_range_inflated == 0 or not np.isfinite(data_range_inflated):
            best_spacing = 0.1 * abs(data_min) if data_min != 0 else 0.1
            best_spacing = max(best_spacing, 1e-9)
        else:
            plot_range = data_range_inflated
            rough_spacing = plot_range / max(1, (target_ticks - 1))
            if rough_spacing <= 1e-9: rough_spacing = 1e-9

            power_of_10 = 10**np.floor(np.log10(rough_spacing))
            possible_spacings = [power_of_10, 2*power_of_10, 5*power_of_10, 10*power_of_10]
            best_spacing = min(possible_spacings, key=lambda s: abs(s - rough_spacing) if rough_spacing != 0 else s)
            best_spacing = max(best_spacing, 1e-9)  

        final_tick_min = np.ceil(data_min / best_spacing) * best_spacing
        final_tick_max = np.floor(data_max / best_spacing) * best_spacing
        
        ticks = np.arange(final_tick_min, final_tick_max + best_spacing * 0.1, best_spacing)

        if best_spacing > 1e-9:
           decimals = max(0, int(-np.floor(np.log10(best_spacing))) + 1)
        else:
           decimals = 10
        ticks = np.round(ticks, decimals)

        if len(ticks) < 2:
            ticks = np.array([final_tick_min, final_tick_max])
            if len(ticks) < 2 or final_tick_min == final_tick_max:
                 ticks = np.array([data_min, data_max])
            ticks = np.round(ticks, decimals)

        return {'limits': [data_min, data_max], 'ticks': ticks}

    @staticmethod
    def apply_x_axis_config(ax: plt.Axes, x_axis_config: Optional[Dict]) -> None:
        if x_axis_config:
            if 'limits' in x_axis_config: ax.set_xlim(x_axis_config['limits'])
            if 'ticks' in x_axis_config: ax.set_xticks(x_axis_config['ticks'])

    @staticmethod
    def apply_y_axis_config(ax: plt.Axes, y_axis_config: Optional[Dict], force_ticks: Optional[int] = None) -> None:
        if y_axis_config:
            if 'limits' in y_axis_config:
                ax.set_ylim(y_axis_config['limits'])
            if force_ticks is not None and 'limits' in y_axis_config:
                ticks = np.linspace(y_axis_config['limits'][0], y_axis_config['limits'][1], force_ticks)
                ax.set_yticks(ticks)
            elif 'ticks' in y_axis_config:
                ax.set_yticks(y_axis_config['ticks'])


# =============================================================================
# CORE CLASSES - PLOT GENERATORS & DRAWERS
# =============================================================================

class PerformanceCurveGenerator:
    """Generates the standard performance vs hyperparameter curve."""
    
    @staticmethod
    def generate(x_values, mean_scores, std_scores, optimal_x, title, xlabel, ylabel, output_path_base, x_scale, preset, grid, clean_ax_spines, legend_frame, optimal_label):
        PlotStyleManager.apply_style()
        fig, ax = plt.subplots(figsize=FIGURE_SIZES.get(preset, FIGURE_SIZES['presentation']))
        
        opt_label = optimal_label if optimal_label is not None else f'Optimal = {optimal_x:.5f}'
        
        ax.plot(x_values, mean_scores, color=COLORS['plot_theme']['main_line'])
        ax.fill_between(x_values, mean_scores - std_scores, mean_scores + std_scores,
                        color=COLORS['plot_theme']['fill_area'], alpha=0.25, label='Std. Dev.')
        
        ax.axvline(optimal_x, linestyle='--', color=COLORS['plot_theme']['accent_line'], label=opt_label)
        
        ax.set(xlabel=xlabel, ylabel=ylabel, title=title, xscale=x_scale)
        ax.legend(frameon=legend_frame)
        
        if clean_ax_spines: PlotStyleManager.clean_spines(ax)
        if grid: ax.grid(True)
        
        plt.tight_layout(rect=TIGHT_LAYOUT_RECTS['default'])
        plt.savefig(output_path_base + '.pdf')
        plt.savefig(output_path_base + '.png')
        plt.close(fig)
        print(f"Performance plot saved to {output_path_base}.[pdf/png]")


class DGDTLComponentDrawer:
    """Encapsulates the logic for drawing individual DGDTL diagnostic subplots."""
    
    def __init__(self, df_results: pd.DataFrame, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None):
        self.df_results = df_results
        self.optimal_dw = optimal_dw
        self.is_nested = is_nested
        self.x_axis_config = x_axis_config

    def draw_performance_std(self, ax: plt.Axes) -> None:
        print("Generating Plot 1: Performance (Validation MSE + Std. Dev.)...")
        if self.df_results.empty or 'avg_selected_MSE_vldt' not in self.df_results.columns or 'std_selected_MSE_vldt' not in self.df_results.columns:
            print("Error in Plot 1: Missing data.")
            ax.set_title('Figure 1: Performance (Missing/No data)')
            return

        raw_x = self.df_results['diversity_weight']
        raw_y_mean = self.df_results['avg_selected_MSE_vldt'].fillna(0)
        raw_y_std = self.df_results['std_selected_MSE_vldt'].fillna(0)
        raw_y_upper, raw_y_lower = raw_y_mean + raw_y_std, raw_y_mean - raw_y_std
        
        y_data_for_limits = pd.concat([raw_y_lower[pd.notna(raw_y_lower)], raw_y_upper[pd.notna(raw_y_upper)]])
        if y_data_for_limits.empty: y_data_for_limits = pd.Series([0, 1])
            
        y_config = PlotMathUtils.calculate_dynamic_axis_config(y_data_for_limits, target_ticks=7, padding_fraction=0.2)
        PlotMathUtils.apply_y_axis_config(ax, y_config)
        
        x_smooth, y_smooth_mean = PlotMathUtils.get_smooth_curve(raw_x, self.df_results['avg_selected_MSE_vldt'])
        _, y_smooth_upper = PlotMathUtils.get_smooth_curve(raw_x, raw_y_upper)
        _, y_smooth_lower = PlotMathUtils.get_smooth_curve(raw_x, raw_y_lower)
        
        ax.plot(x_smooth, y_smooth_mean, color=COLORS['plot_theme']['main_line'])
        ax.fill_between(x_smooth, y_smooth_lower, y_smooth_upper, color=COLORS['plot_theme']['fill_area'], alpha=0.25, label='Std. Dev.')
        
        if self.optimal_dw is not None:
            ax.axvline(self.optimal_dw, linestyle='--', color=COLORS['plot_theme']['accent_line'], label=f'Optimal DW = {self.optimal_dw:.4f}')
            
        ax.set(title='Figure 1. DGDTL Performance ', xlabel='Diversity Weight (DW)', ylabel='Mean NCV Score MSE (Validation)')
        ax.legend(frameon=False, loc='best')
        PlotMathUtils.apply_x_axis_config(ax, self.x_axis_config)

    def draw_stability(self, ax: plt.Axes) -> None:
        print("Generating Plot 2: Scanner Stability...")
        if self.df_results.empty or 'success_rate' not in self.df_results.columns:
            print("Error in Plot 2: Missing data.")
            ax.set_title('Figure 2: Stability (Missing/No data)')
            return
            
        x = self.df_results['diversity_weight']
        y = self.df_results['success_rate'].fillna(0) * 100 
        
        x_smooth, y_smooth = PlotMathUtils.get_smooth_curve(x, y)
        ax.plot(x_smooth, y_smooth, '-', color=COLORS['greens'][2], label='Success Rate (Valid Solutions)')
                
        ax.set(title='Figure 2. DGDTL Stability (Valid Solutions)', xlabel='Diversity Weight (DW)', ylabel='Success Rate (%)')
        if not y.empty:
            min_y = y.min()
            ax.set_ylim(bottom=min(min_y - 5, 90) if pd.notna(min_y) else 90, top=101)
                
        ax.legend(frameon=False, loc='best')
        PlotMathUtils.apply_x_axis_config(ax, self.x_axis_config)

    def draw_components(self, ax1: plt.Axes) -> None:
        print("Generating Plot 3: Component Diagnosis...")
        if self.df_results.empty or 'avg_selected_MSE_train' not in self.df_results.columns:
            print("Error in Plot 3: Missing data.")
            ax1.set_title('Figure 3: Components (Missing/No data)')
            return

        PlotStyleManager.set_palette('impact')     
        
        color1 = COLORS['impact'][0]
        raw_x = self.df_results['diversity_weight']
        raw_y_train = self.df_results['avg_selected_MSE_train'] 
        
        y_config_train = PlotMathUtils.calculate_dynamic_axis_config(raw_y_train, target_ticks=8, padding_fraction=0.2)
        PlotMathUtils.apply_y_axis_config(ax1, y_config_train)
        
        ax1_yticks, ax1_ylim = ax1.get_yticks(), ax1.get_ylim()
        x_smooth_train, y_smooth_train = PlotMathUtils.get_smooth_curve(raw_x, raw_y_train)
        
        l1 = ax1.plot(x_smooth_train, y_smooth_train, '-', color=color1, label='MSE (Train)')
        ax1.set(xlabel='Diversity Weight (DW)', ylabel='Mean MSE (Train)', title='Figure 3. DGDTL: Component Diagnosis (Trade-off)')
        ax1.yaxis.label.set_color(color1)
        ax1.tick_params(axis='y', colors=color1)
        lines, labels = l1, [l.get_label() for l in l1]

        if 'avg_selected_beta_variance' in self.df_results and self.df_results['avg_selected_beta_variance'].notna().any():
            raw_y_var = self.df_results['avg_selected_beta_variance']
            color2 = COLORS['impact'][1]
            ax2 = ax1.twinx()        

            y_config_var = PlotMathUtils.calculate_dynamic_axis_config(raw_y_var, target_ticks=8, padding_fraction=0.2)
            ax2.set_ylim(y_config_var['limits'])
            ax2_ylim = ax2.get_ylim()

            ax1_range = ax1_ylim[1] - ax1_ylim[0]
            ax1_tick_fractions = np.full_like(ax1_yticks, 0.5) if ax1_range == 0 else (ax1_yticks - ax1_ylim[0]) / ax1_range
                
            ax2_range = ax2_ylim[1] - ax2_ylim[0]
            ax2_new_ticks = np.full_like(ax1_tick_fractions, ax2_ylim[0]) if ax2_range == 0 else ax2_ylim[0] + ax1_tick_fractions * ax2_range
                
            ax2.set_yticks(ax2_new_ticks)
            x_smooth_var, y_smooth_var = PlotMathUtils.get_smooth_curve(raw_x, raw_y_var)
            
            l2 = ax2.plot(x_smooth_var, y_smooth_var, '-', color=color2, label='Beta Variance')
            ax2.set(ylabel='Mean Beta Variance')
            ax2.yaxis.label.set_color(color2)
            ax2.tick_params(axis='y', colors=color2)
            PlotMathUtils.apply_x_axis_config(ax2, self.x_axis_config)    

            lines += l2
            labels += [l.get_label() for l in l2]

        if self.optimal_dw is not None:
            ax1.axvline(self.optimal_dw, linestyle='--', color='black', label=f'Optimal DW = {self.optimal_dw:.4f}')     

        ax1.legend(lines, labels, loc='best', frameon=False)    
        PlotMathUtils.apply_x_axis_config(ax1, self.x_axis_config)
        PlotStyleManager.set_palette() # Reset

    def draw_precision_robustness(self, ax: plt.Axes) -> None:
        print("Generating Plot 4: Performance (Precision vs. Robustness)...")
        if self.df_results.empty:
            ax.set_title('Figure 4: Precision vs. Robustness (No data)')
            return

        if 'avg_selected_MSE_vldt' in self.df_results.columns:
            y1, y1_label = self.df_results['avg_selected_MSE_vldt'], 'TIE Score'
        elif 'avg_vldt_mse' in self.df_results.columns:
            y1, y1_label = self.df_results['avg_vldt_mse'], 'Mean Score MSE (Validation)'
        else:
            print("Error in Plot 4: Missing data.")
            ax.set_title('Figure 4: Performance (Missing key data)')
            return
            
        if 'pct_champions' in self.df_results.columns:
            y2, y2_label = self.df_results['pct_champions'] * 100, '% Folds with Elite Champions'
        elif 'success_rate' in self.df_results.columns: 
            y2, y2_label = self.df_results['success_rate'] * 100, 'Success Rate (%)' 
        else:
            y2, y2_label = pd.Series([0] * len(self.df_results)), 'Robustness (Missing Data)'

        x = self.df_results['diversity_weight']
        color = 'tab:blue'
        ax.set_xlabel('Diversity Weight (DW)')
        ax.set_ylabel(y1_label, color=color)
        
        x_smooth, y_smooth = PlotMathUtils.get_smooth_curve(x, y1)
        l1 = ax.plot(x_smooth, y_smooth, '-', color=color, zorder=10, label=y1_label)
        ax.tick_params(axis='y', labelcolor=color)

        ax2 = ax.twinx()
        x_np, y2_np = x.to_numpy(), y2.fillna(0).to_numpy()
        valid_mask = ~np.isnan(x_np) & ~np.isnan(y2_np)
        x_np, y2_np = x_np[valid_mask], y2_np[valid_mask]
        
        color = 'tab:green'
        ax2.set_ylabel(y2_label, color=color)
        
        if len(x_np) > 1:
            diffs = np.diff(x_np)
            bar_width = np.mean(diffs) * 0.8 if len(diffs) > 0 and np.mean(diffs) > 0 else 0.05
        else:
            bar_width = 0.05 if len(x_np) == 1 else 0
                
        l2 = ax2.bar(x_np, y2_np, alpha=0.3, color=color, width=bar_width, label=y2_label)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(0, 105)  

        if self.optimal_dw is not None:
            ax.axvline(self.optimal_dw, color='black', linestyle=':', linewidth=2, label=f'Optimal DW ({self.optimal_dw:.3f})')
            
        ax.set_title('Figure 4. DGDTL: Diversity Weight Tuning (Precision vs. Robustness)')
        lines, labels = l1, [l.get_label() for l in l1]
        ax2.legend(lines + [l2], labels + [l2.get_label()], loc='best', frameon=False) 
        PlotMathUtils.apply_x_axis_config(ax, self.x_axis_config)


class CVAnalysisPanelGenerator:
    """Orchestrates the creation of the 2x2 CV analysis panel."""
    
    @staticmethod
    def generate(df_results, title, output_path_base, grid, clean_ax_spines, optimal_dw, is_nested, x_axis_config):
        PlotStyleManager.apply_style()
        fig, axes = plt.subplots(2, 2, figsize=FIGURE_SIZES.get('diagnostic_panel', (12, 8)))
        fig.suptitle(title, weight='bold', fontsize=14) 

        x_config = x_axis_config
        if x_config is None and (df_results is not None and not df_results.empty):
            print("[Info] Auto-calculating x_axis_config for the panel...")
            try:
                x_config = PlotMathUtils.calculate_dynamic_axis_config(df_results['diversity_weight'])
            except Exception as e:
                print(f"Warning: Could not auto-calculate x-axis config. Using defaults. {e}")
                x_config = None 

        drawer = DGDTLComponentDrawer(df_results, optimal_dw, is_nested, x_config)
        drawer.draw_performance_std(axes[0, 0])
        drawer.draw_stability(axes[0, 1])                        
        drawer.draw_components(axes[1, 0])  
        drawer.draw_precision_robustness(axes[1, 1]) 

        for row in axes:
            for ax in row:
                if clean_ax_spines:
                    PlotStyleManager.clean_spines(ax)
                    ax2 = next((sibling for sibling in ax.get_shared_x_axes().get_siblings(ax) if sibling != ax), None)
                    if ax2:
                        PlotStyleManager.clean_spines(ax2, left=False, right=True, top=True, bottom=True)
                if grid:
                    ax.grid(True, linestyle='--', alpha=0.6)
        
        plt.tight_layout(rect=TIGHT_LAYOUT_RECTS.get('diagnostic_panel', [0, 0.03, 1, 0.94]))
        plt.savefig(output_path_base + '.pdf')
        plt.savefig(output_path_base + '.png')
        plt.close(fig)
        print(f"\nAnalysis panel saved to {output_path_base}.[pdf/png]")


class IndividualDGDTLPlotGenerator:
    """Wrapper class to generate individual plots using the DGDTLComponentDrawer."""
    
    @staticmethod
    def generate(plot_type: str, df_results: pd.DataFrame, output_path_base: str, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None, grid: bool = False, clean_ax_spines: bool = False):
        PlotStyleManager.apply_style()
        fig, ax = plt.subplots(figsize=FIGURE_SIZES.get('presentation', (8, 6))) 
        drawer = DGDTLComponentDrawer(df_results, optimal_dw, is_nested, x_axis_config)

        if plot_type == 'performance_std':
            drawer.draw_performance_std(ax)
        elif plot_type == 'stability':
            drawer.draw_stability(ax)
        elif plot_type == 'components':
            drawer.draw_components(ax)
        elif plot_type == 'precision_robustness':
            drawer.draw_precision_robustness(ax)
        
        if clean_ax_spines: 
            PlotStyleManager.clean_spines(ax)
            if plot_type in ['components', 'precision_robustness']:
                ax2 = next((s for s in ax.get_shared_x_axes().get_siblings(ax) if s != ax), None)
                if ax2: PlotStyleManager.clean_spines(ax2, left=False, right=True, top=True, bottom=True)

        if grid: ax.grid(True, linestyle='--', alpha=0.6)
        
        plt.tight_layout(rect=TIGHT_LAYOUT_RECTS.get('default', [0, 0, 1, 1]))
        plt.savefig(output_path_base + '.pdf')
        plt.savefig(output_path_base + '.png')
        plt.close(fig)
        print(f"Individual plot ({plot_type}) saved to {output_path_base}.[pdf/png]")


class DiagnosticPlotter:
    """Generates the statistical diagnostic panel."""
    
    @staticmethod
    def generate(fitted_vals, residuals, leverage, num_predictors, title, output_path_base, grid, clean_ax_spines, legend_frame):
        PlotStyleManager.apply_style()
        PlotStyleManager.set_palette('grayscale')
        fig, axes = plt.subplots(2, 2, figsize=FIGURE_SIZES['diagnostic_panel'])
        
        std_residuals = residuals / np.std(residuals, ddof=1)
        point_color = COLORS['plot_theme']['point_marker']
        line_color = COLORS['reds'][3]

        ax = axes[0, 0]
        ax.scatter(fitted_vals, residuals, alpha=0.9, c=point_color, edgecolors='white')
        ax.plot(*sm.nonparametric.lowess(residuals, fitted_vals).T, color=line_color)
        ax.axhline(0, linestyle='--', color='black', lw=0.8, alpha=0.9)
        ax.set(title='Residuals vs Fitted', xlabel='Fitted values', ylabel='Residuals')

        ax = axes[0, 1]
        sm.qqplot(std_residuals, line='45', fit=True, ax=ax, markerfacecolor=point_color, markeredgecolor='white', alpha=0.9)
        ax.get_lines()[1].set(color=line_color, linewidth=1.5)
        ax.set(title='Normal Q-Q', xlabel='Theoretical Quantiles', ylabel='Standardized Residuals')

        ax = axes[1, 0]
        sqrt_std_resid = np.sqrt(np.abs(std_residuals))
        ax.scatter(fitted_vals, sqrt_std_resid, alpha=0.9, c=point_color, edgecolors='white')
        ax.plot(*sm.nonparametric.lowess(sqrt_std_resid, fitted_vals).T, color=line_color)
        ax.set(title='Scale-Location', xlabel='Fitted values', ylabel=r'$\sqrt{|Standardized\ Residuals|}$')

        ax = axes[1, 1]
        ax.scatter(leverage, std_residuals, alpha=0.9, c=point_color, edgecolors='white')
        ax.axhline(0, linestyle='-', color='black', lw=0.8, alpha=0.7)
        
        min_lev = np.min(leverage[leverage > 0]) if np.any(leverage > 0) else 1e-6
        h_vals = np.linspace(min_lev, np.max(leverage), 100)
        
        for d, style in zip([0.5, 1.0], [':', '--']):
            cooks_arg = d * num_predictors * (1 - h_vals) / h_vals
            cooks_d = np.sqrt(np.maximum(0, cooks_arg))
            ax.plot(h_vals, cooks_d, linestyle=style, color=line_color, label=f"Cook's D ({d})")
            ax.plot(h_vals, -cooks_d, linestyle=style, color=line_color)
            
        ax.legend(frameon=legend_frame, loc='upper right')
        ax.set(title='Residuals vs Leverage', xlabel='Leverage', ylabel='Standardized Residuals')
        
        for ax_row in axes:
            for ax_elem in ax_row:
                if clean_ax_spines: PlotStyleManager.clean_spines(ax_elem)
                if grid: ax_elem.grid(True)

        fig.suptitle(title)
        plt.tight_layout(rect=TIGHT_LAYOUT_RECTS['diagnostic_panel'])
        plt.savefig(output_path_base + '.pdf')
        plt.savefig(output_path_base + '.png')
        plt.close(fig)
        #print(f"Diagnostic plots saved to {output_path_base}.[pdf/png]")


class ParityPlotter:
    """Generates a publication-quality parity plot."""
    
    @staticmethod
    def generate(y_true, y_pred, groups, title, xlabel, ylabel, output_path_base, preset, grid, clean_ax_spines, legend_frame, legend_fontsize):
        PlotStyleManager.apply_style()
        fig, ax = plt.subplots(figsize=FIGURE_SIZES.get(preset, (7, 7)))

        color_map = {'Training': COLORS['blues'][4], 'Validation': COLORS['impact'][2], 'Testing': COLORS['greens'][3]}
        legend_order = ['Training', 'Validation', 'Testing']

        for group in legend_order:
            if group in np.unique(groups):
                idx = (groups == group)
                ax.scatter(y_true[idx], y_pred[idx], s=30, edgecolor='k', linewidth=0.6, label=group, color=color_map.get(group, COLORS['neutrals']['points']))

        lims = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
        ax.plot(lims, lims, 'k--', alpha=0.85, zorder=0, linewidth=0.8)
        ax.set(xlim=lims, ylim=lims, xlabel=xlabel, ylabel=ylabel, title=title)
        
        ax.legend(title='Dataset', frameon=legend_frame, fontsize=legend_fontsize)
        ax.set_aspect('equal', adjustable='box')

        if clean_ax_spines: PlotStyleManager.clean_spines(ax)
        if grid: ax.grid(True)
        
        plt.tight_layout(rect=TIGHT_LAYOUT_RECTS['default'])
        plt.savefig(output_path_base + '.pdf')
        plt.savefig(output_path_base + '.png')
        plt.close(fig)
        #print(f"Parity plot saved to {output_path_base}.[pdf/png]")


class HeatmapPlotter:
    """Generates a 2D search heatmap."""
    
    @staticmethod
    def generate(cv_results, param_x, param_y, optimal_params, title, output_path_base):
        results = pd.DataFrame(cv_results)
        results[param_x], results[param_y] = pd.to_numeric(results[param_x]), pd.to_numeric(results[param_y])
        pivot = results.pivot_table(index=param_y, columns=param_x, values='mean_test_score')
        
        fig, ax = plt.subplots(figsize=FIGURE_SIZES['heatmap'])
        sns.heatmap(-pivot, cmap="viridis_r", ax=ax)
        
        y_values = pivot.index
        num_y_ticks = min(8, len(y_values))
        log_spaced_y_values = np.logspace(np.log10(y_values.min()), np.log10(y_values.max()), num=num_y_ticks)
        y_tick_locations = [np.argmin(np.abs(y_values - val)) for val in log_spaced_y_values]
        y_tick_labels = [f'{val:.3f}' for val in log_spaced_y_values] 
        
        ax.set_yticks(np.array(y_tick_locations) + 0.5)
        ax.set_yticklabels(y_tick_labels, rotation=0)

        xticklabels = pivot.columns
        num_x_ticks = 8
        step = max(1, len(xticklabels) // num_x_ticks)
        tick_locations = np.arange(0, len(xticklabels), step)
        tick_labels = [f'{xticklabels[i]:.3f}' for i in tick_locations]
        
        ax.set_xticks(tick_locations + 0.5)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')
        
        if optimal_params:
            optimal_y_val, optimal_x_val = optimal_params[param_y.replace('param_', '')], optimal_params[param_x.replace('param_', '')]
            y_idx, x_idx = np.argmin(np.abs(pivot.index - optimal_y_val)), np.argmin(np.abs(pivot.columns - optimal_x_val))
            ellipse = Ellipse(xy=(x_idx + 0.5, y_idx + 0.5), width=1.5, height=1.5, edgecolor='red', fc='None', lw=2.5, linestyle='--')
            ax.add_patch(ellipse)

        ax.set_title(title)
        ax.set_xlabel(param_x.replace('param_', '').replace('_', ' ').title())
        ax.set_ylabel(param_y.replace('param_', '').replace('_', ' ').title())
        
        plt.tight_layout()
        plt.savefig(output_path_base + '.pdf')
        plt.savefig(output_path_base + '.png', dpi=300)
        plt.close(fig)
        print(f"Grid search heatmap saved to: {output_path_base}.png")


class SolutionSpacePlotter:
    """Generates the DGDTL Solution Space scatter plot."""
    
    @staticmethod
    def generate(valid_solutions_info, baseline_mse_train, baseline_mse_vldt, best_dgdtl_solution, params, output_dir, output_filename):
        print(f"\n{Colors.CYAN}--- Generating Solution Space Plot: {output_filename} ---{Colors.ENDC}")
        if not valid_solutions_info:
            print("No valid solutions to plot.")
            return

        PlotStyleManager.apply_style()
        df_valid = pd.DataFrame(valid_solutions_info)
        color_metric = 'PEL_Metric' if 'PEL_Metric' in df_valid.columns and df_valid['PEL_Metric'].notna().any() else None
        
        fig, ax = plt.subplots(figsize=FIGURE_SIZES.get('presentation', (8, 7)))
        
        all_vals = pd.concat([df_valid['MSE_train'], df_valid['MSE_vldt']]).tolist() + [baseline_mse_train, baseline_mse_vldt]
        g_min, g_max = min(all_vals) * 0.95, max(all_vals) * 1.05
        ax.plot([g_min, g_max], [g_min, g_max], color='black', linestyle='--', linewidth=1.0, alpha=0.7, zorder=0, label='Generalization Parity\n($MSE_{vldt} = MSE_{train}$)')

        min_limit, max_limit = params.get('mse_min_limit'), params.get('mse_max_limit')
        if min_limit is not None and max_limit is not None:
            ax.axvspan(min_limit, max_limit, color=COLORS['greens'][0], alpha=0.15, zorder=-1, label='Search Tunnel')
            ax.axvline(min_limit, color=COLORS['greens'][2], linestyle=':', linewidth=1.5, label=f'Tunnel Min ({min_limit:.3f})')
            ax.axvline(max_limit, color=COLORS['greens'][2], linestyle=':', linewidth=1.5, label=f'Tunnel Max ({max_limit:.3f})')

        if color_metric:
            cmap = plt.cm.get_cmap('viridis_r') 
            points = ax.scatter(df_valid['MSE_train'], df_valid['MSE_vldt'], c=df_valid[color_metric], cmap=cmap, alpha=0.8, s=70, edgecolors='w', linewidth=0.5, label="DGDTL Candidates", zorder=2)
            cbar = fig.colorbar(points, ax=ax, pad=0.02)
            cbar.set_label('Probabilistic Elastic Loss (PEL)', rotation=270, labelpad=20, fontsize=10)
            cbar.ax.tick_params(labelsize=8)
        else:
            ax.scatter(df_valid['MSE_train'], df_valid['MSE_vldt'], color=COLORS['plot_theme']['main_line'], alpha=0.7, s=70, edgecolors='k', linewidth=0.5, label="DGDTL Candidates", zorder=2)
        
        ax.scatter(baseline_mse_train, baseline_mse_vldt, marker='o', s=50, facecolors=COLORS['reds'][2], edgecolors='k', linewidth=1.5, label="Baseline Model", zorder=5)
        if best_dgdtl_solution:
            ax.scatter(best_dgdtl_solution['MSE_train'], best_dgdtl_solution['MSE_vldt'], marker='o', s=80, facecolors=COLORS['violets'][1], edgecolors='k', linewidth=2.0, label="Champion", zorder=6, alpha=0.9)

        ax.set_xlabel("Training MSE", fontsize=12)
        ax.set_ylabel("Validation MSE", fontsize=12)
        
        region_type = "Focused" if "run2" in output_filename.lower() else "Exploratory"
        ax.set_title(f"Solution Space Analysis: {region_type} Region", fontweight='bold', pad=15, fontsize=14)
        
        ax.legend(loc='best', frameon=True, fontsize=9, fancybox=True, edgecolor='gray', framealpha=0.9)
        ax.grid(True, which='both', linestyle=':', linewidth=0.5, color='gray', alpha=0.5)

        all_x = df_valid['MSE_train'].tolist() + [baseline_mse_train]
        all_y = df_valid['MSE_vldt'].tolist() + [baseline_mse_vldt]
        if best_dgdtl_solution:
            all_x.append(best_dgdtl_solution['MSE_train'])
            all_y.append(best_dgdtl_solution['MSE_vldt'])
        
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        x_pad = (x_max - x_min) * 0.1 if (x_max - x_min) > 0 else x_min * 0.1
        y_pad = (y_max - y_min) * 0.1 if (y_max - y_min) > 0 else y_min * 0.1
        
        ax.set_xlim(x_min - x_pad, x_max + x_pad)
        ax.set_ylim(y_min - y_pad, y_max + y_pad)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, output_filename)
        plt.savefig(plot_path, dpi=300)
        plt.close(fig)
        print(f" > Solution Space Plot saved to: {plot_path}")


class GoldilocksDonutPlotter:
    """Generates the DGDTL Goldilocks Donut visualization."""
    
    @staticmethod
    def _draw_architectural_limit(ax, angle_deg, radius_plot, radius_real_label, color, base_plot, label_offset_r=0.0075):
        rad = np.radians(angle_deg)
        ax.plot([rad, rad], [base_plot, radius_plot], color=color, linewidth=1.2, linestyle='-', alpha=0.8, zorder=10)
        
        arc_width = 0.06 
        theta_arc = np.linspace(rad - arc_width, rad + arc_width, 15)
        ax.plot(theta_arc, [radius_plot]*15, color=color, linewidth=2.5, solid_capstyle='round', zorder=11)
        
        txt = radius_real_label if isinstance(radius_real_label, str) else f"{radius_real_label:.2f}"
        rot = angle_deg - 90 
        text_radius = radius_plot + label_offset_r

        ax.text(rad, text_radius, txt, color=color, fontsize=10, fontweight='bold', ha='center', va='bottom', rotation=rot, bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=2, boxstyle='round,pad=0.15'))

    @classmethod
    def generate(cls, solutions_run1, solutions_run2, baseline_mse, params_run1, params_run2, output_dir, champion_run1, champion_run2, output_filename):
        print(f"\n{Colors.CYAN}--- Generating Goldilocks Donut Plot (Visually Optimized) ---{Colors.ENDC}")
        if not solutions_run1 and not solutions_run2: return

        all_sols = []
        if solutions_run1:
            for s in solutions_run1: s['Run'] = 1; all_sols.append(s)
        if solutions_run2:
            for s in solutions_run2: s['Run'] = 2; all_sols.append(s)
        df = pd.DataFrame(all_sols)
        
        safe_baseline_mse = baseline_mse if baseline_mse > 1e-9 else 1.0

        if params_run1 and params_run1.get('mse_min_limit') is not None:
            r1_min_real, r1_max_real = params_run1['mse_min_limit'] / safe_baseline_mse, params_run1['mse_max_limit'] / safe_baseline_mse
        else:
            tol = params_run1.get('TOLERANCE_FACTOR', 0.3) if params_run1 else 0.3
            r1_min_real, r1_max_real = min(1.0, 1.0 + tol), max(1.0, 1.0 + tol)
            
        if params_run2 and params_run2.get('mse_min_limit') is not None:
            r2_min_real, r2_max_real = params_run2['mse_min_limit'] / safe_baseline_mse, params_run2['mse_max_limit'] / safe_baseline_mse
        else:
            r2_min_real, r2_max_real = r1_min_real, r1_max_real

        R_OFFSET = 0.90 
        base_plot = 1.0 - R_OFFSET
        r1_min_plot, r1_max_plot = r1_min_real - R_OFFSET, r1_max_real - R_OFFSET
        r2_min_plot, r2_max_plot = r2_min_real - R_OFFSET, r2_max_real - R_OFFSET

        r_plot = (df['MSE_train'] / baseline_mse) - R_OFFSET
        rho_global = df['MSE_vldt'] / df['MSE_train']
        rho_min, rho_max = rho_global.min(), rho_global.max()
        
        def get_theta(mse_train, mse_vldt):
            return 0 if rho_max == rho_min else (mse_vldt / mse_train - rho_min) / (rho_max - rho_min) * 1.8 * np.pi

        theta = df.apply(lambda row: get_theta(row['MSE_train'], row['MSE_vldt']), axis=1)
        
        plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 12, 'axes.linewidth': 1.2})
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
        ax.set_axis_off()
        theta_range = np.linspace(0, 2*np.pi, 600)
        
        ax.plot(theta_range, [base_plot]*600, color='#D62728', linestyle='-', linewidth=2.0, zorder=5)
        ax.fill_between(theta_range, r1_min_plot, r1_max_plot, color='#A8D5BA', alpha=0.25, zorder=0)
        ax.plot(theta_range, [r1_min_plot]*600, color='#2E8B57', linestyle='--', linewidth=1.5, alpha=0.5)
        ax.plot(theta_range, [r1_max_plot]*600, color='#2E8B57', linestyle='--', linewidth=1.5, alpha=0.5)
        ax.fill_between(theta_range, r2_min_plot, r2_max_plot, color='#89CFF0', alpha=0.25, zorder=1)
        ax.plot(theta_range, [r2_min_plot]*600, color='#336699', linestyle='--', linewidth=1.5, alpha=0.5)
        ax.plot(theta_range, [r2_max_plot]*600, color='#336699', linestyle='--', linewidth=1.5, alpha=0.5)

        cls._draw_architectural_limit(ax, 15, r1_min_plot, r1_min_real, '#2E8B57', base_plot)
        cls._draw_architectural_limit(ax, 65, r1_max_plot, r1_max_real, '#2E8B57', base_plot)
        ax.text(np.radians(40), r1_min_plot + 0.075, "Exploratory\nRegion", color='#2E8B57', fontsize=10, fontweight='bold', ha='center', va='bottom')

        cls._draw_architectural_limit(ax, 165, r2_min_plot, r2_min_real, '#336699', base_plot)
        cls._draw_architectural_limit(ax, 115, r2_max_plot, r2_max_real, '#336699', base_plot)
        ax.text(np.radians(140), r2_max_plot - 0.04, "Focused\nRegion", color='#336699', fontsize=10, fontweight='bold', ha='center', va='top')
        
        ax.text(0, base_plot - 0.05, "Baseline", color='#D62728', fontsize=9, fontweight='bold', ha='center', va='center', bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1))

        idx_r1, idx_r2 = df['Run'] == 1, df['Run'] == 2
        if any(idx_r1): ax.scatter(theta[idx_r1], r_plot[idx_r1], c='green', alpha=0.25, s=40, marker='o', edgecolors='none', zorder=2)
        if any(idx_r2): ax.scatter(theta[idx_r2], r_plot[idx_r2], c='#4682B4', alpha=0.7, s=40, marker='o', edgecolors='white', linewidth=0.5, zorder=3)

        if champion_run1:
            r_c1_plot = (champion_run1['MSE_train'] / baseline_mse) - R_OFFSET
            t_c1 = get_theta(champion_run1['MSE_train'], champion_run1['MSE_vldt'])
            ax.plot([t_c1, t_c1], [base_plot, r_c1_plot], color='#32CD32', linestyle='--', linewidth=1.5, zorder=15)
            ax.scatter(t_c1, r_c1_plot, marker='o', s=100, c='#32CD32', edgecolors='black', linewidth=1.5, zorder=16)

        if champion_run2:
            r_c2_plot = (champion_run2['MSE_train'] / baseline_mse) - R_OFFSET
            t_c2 = get_theta(champion_run2['MSE_train'], champion_run2['MSE_vldt'])
            ax.plot([t_c2, t_c2], [base_plot, r_c2_plot], color='#336699', linestyle='--', linewidth=1.5, zorder=15)
            ax.scatter(t_c2, r_c2_plot, marker='o', s=100, c='blue', edgecolors='black', linewidth=2.0, zorder=16)

        ax.set_ylim(0.0, max(r1_max_plot, r2_max_plot, r_plot.max()) * 1.15)
        legend_elements = [
            Patch(facecolor='#A8D5BA', edgecolor='#2E8B57', alpha=0.3, label='Exploratory Zone (Run 1)'),
            Patch(facecolor='#89CFF0', edgecolor='#336699', alpha=0.3, label='Focused Zone (Run 2)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=6, alpha=0.5, label='Run 1 Solutions'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#4682B4', markersize=6, alpha=0.8, label='Run 2 Solutions'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#32CD32', markersize=8, markeredgecolor='k', label='Run 1 Champion'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=8, markeredgewidth=2, markeredgecolor='k', label='Run 2 Champion'),
            Line2D([0], [0], color='#D62728', lw=2, label='Baseline Reference')
        ]

        plt.title("Adaptive Tunnel Topology", fontsize=16, fontweight='bold', y=0.96)
        ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=3, frameon=False, fontsize=10)
        
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f" > Goldilocks Donut plot saved to: {output_filename}")


# =============================================================================
# ORIGINAL PUBLIC API (WRAPPERS / FACADES)
# =============================================================================

def apply_style() -> None:
    PlotStyleManager.apply_style()

def set_palette(name: str = 'impact') -> None:
    PlotStyleManager.set_palette(name)

def clean_spines(ax: plt.Axes, left: bool = True, right: bool = True, top: bool = True, bottom: bool = True) -> None:
    PlotStyleManager.clean_spines(ax, left, right, top, bottom)

def get_smooth_curve(x_raw: Union[pd.Series, np.ndarray, List[float]], y_raw: Union[pd.Series, np.ndarray, List[float]]) -> Tuple[np.ndarray, np.ndarray]:
    return PlotMathUtils.get_smooth_curve(x_raw, y_raw)

def calculate_dynamic_axis_config(data_series: Union[pd.Series, np.ndarray], target_ticks: int = 9, padding_fraction: float = 0.05) -> Dict[str, Union[List[float], np.ndarray]]:
    return PlotMathUtils.calculate_dynamic_axis_config(data_series, target_ticks, padding_fraction)

calculate_dynamic_x_config = calculate_dynamic_axis_config

def _apply_x_axis_config(ax: plt.Axes, x_axis_config: Optional[Dict]) -> None:
    PlotMathUtils.apply_x_axis_config(ax, x_axis_config)

def _apply_y_axis_config(ax: plt.Axes, y_axis_config: Optional[Dict], force_ticks: Optional[int] = None) -> None:
    PlotMathUtils.apply_y_axis_config(ax, y_axis_config, force_ticks)
            
def plot_performance_curve(x_values, mean_scores, std_scores, optimal_x, title, xlabel, ylabel, output_path_base, x_scale='linear', preset='single_col', grid=False, clean_ax_spines=True, legend_frame=False, optimal_label=None) -> None:
    PerformanceCurveGenerator.generate(x_values, mean_scores, std_scores, optimal_x, title, xlabel, ylabel, output_path_base, x_scale, preset, grid, clean_ax_spines, legend_frame, optimal_label)

def _draw_performance_std(ax: plt.Axes, df_results: pd.DataFrame, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None) -> None:
    drawer = DGDTLComponentDrawer(df_results, optimal_dw, is_nested, x_axis_config)
    drawer.draw_performance_std(ax)

def _draw_stability(ax: plt.Axes, df_results: pd.DataFrame, x_axis_config: Optional[Dict] = None) -> None:
    drawer = DGDTLComponentDrawer(df_results, x_axis_config=x_axis_config)
    drawer.draw_stability(ax)

def _draw_components(ax1: plt.Axes, df_results: pd.DataFrame, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None) -> None:
    drawer = DGDTLComponentDrawer(df_results, optimal_dw, is_nested, x_axis_config)
    drawer.draw_components(ax1)

def _draw_performance(ax: plt.Axes, df_results: pd.DataFrame, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None) -> None:
    drawer = DGDTLComponentDrawer(df_results, optimal_dw, is_nested, x_axis_config)
    drawer.draw_precision_robustness(ax)

def plot_performance_std(df_results: pd.DataFrame, output_path_base: str, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None, grid: bool = False, clean_ax_spines: bool = False) -> None:
    IndividualDGDTLPlotGenerator.generate('performance_std', df_results, output_path_base, optimal_dw, is_nested, x_axis_config, grid, clean_ax_spines)

def plot_stability(df_results: pd.DataFrame, output_path_base: str, x_axis_config: Optional[Dict] = None, grid: bool = False, clean_ax_spines: bool = False) -> None:
    IndividualDGDTLPlotGenerator.generate('stability', df_results, output_path_base, None, False, x_axis_config, grid, clean_ax_spines)

def plot_components(df_results: pd.DataFrame, output_path_base: str, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None, grid: bool = False, clean_ax_spines: bool = False) -> None:
    IndividualDGDTLPlotGenerator.generate('components', df_results, output_path_base, optimal_dw, is_nested, x_axis_config, grid, clean_ax_spines)

def plot_precision_robustness(df_results: pd.DataFrame, output_path_base: str, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None, grid: bool = False, clean_ax_spines: bool = False) -> None:
    IndividualDGDTLPlotGenerator.generate('precision_robustness', df_results, output_path_base, optimal_dw, is_nested, x_axis_config, grid, clean_ax_spines)

def plot_cv_analysis_panel(df_results: pd.DataFrame, title: str, output_path_base: str, grid: bool = False, clean_ax_spines: bool = False, optimal_dw: Optional[float] = None, is_nested: bool = False, x_axis_config: Optional[Dict] = None) -> None:
    CVAnalysisPanelGenerator.generate(df_results, title, output_path_base, grid, clean_ax_spines, optimal_dw, is_nested, x_axis_config)

def plot_diagnostics(fitted_vals, residuals, leverage, num_predictors, title, output_path_base, grid=False, clean_ax_spines=True, legend_frame=False) -> None:
    DiagnosticPlotter.generate(fitted_vals, residuals, leverage, num_predictors, title, output_path_base, grid, clean_ax_spines, legend_frame)
    
def plot_parity(y_true, y_pred, groups, title, xlabel, ylabel, output_path_base, preset='parity_plot', grid=False, clean_ax_spines=True, legend_frame=False, legend_fontsize=None) -> None:
    ParityPlotter.generate(y_true, y_pred, groups, title, xlabel, ylabel, output_path_base, preset, grid, clean_ax_spines, legend_frame, legend_fontsize)
    
def plot_2d_search_heatmap(cv_results, param_x, param_y, optimal_params, title, output_path_base) -> None:
    HeatmapPlotter.generate(cv_results, param_x, param_y, optimal_params, title, output_path_base)

def plot_solution_space(valid_solutions_info, baseline_mse_train, baseline_mse_vldt, best_dgdtl_solution, params, output_dir, output_filename="DGDTL_Solution_Space_Plot.png") -> None:
    SolutionSpacePlotter.generate(valid_solutions_info, baseline_mse_train, baseline_mse_vldt, best_dgdtl_solution, params, output_dir, output_filename)

def plot_goldilocks_donut(solutions_run1, solutions_run2, baseline_mse, params_run1, params_run2, output_dir, champion_run1=None, champion_run2=None, output_filename="DGDTL_Goldilocks_Donut.png") -> None:
    GoldilocksDonutPlotter.generate(solutions_run1, solutions_run2, baseline_mse, params_run1, params_run2, output_dir, champion_run1, champion_run2, output_filename)
