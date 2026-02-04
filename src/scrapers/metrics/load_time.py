"""Load time metrics with statistical robustness."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import statistics

import numpy as np


@dataclass
class LoadTimeMetrics:
    """Statistical metrics for load time measurements."""
    
    samples: List[float] = field(default_factory=list)
    median: float = 0.0
    trimmed_mean: float = 0.0  # Mean after removing outliers
    percentile_90: float = 0.0
    percentile_95: float = 0.0
    std_dev: float = 0.0
    iqr: float = 0.0  # Interquartile range
    coefficient_of_variation: float = 0.0  # CV = std_dev / mean
    confidence_score: float = 0.0  # How reliable is this measurement?
    
    def calculate(self) -> None:
        """Calculate all statistical metrics from samples."""
        if len(self.samples) < 2:
            if self.samples:
                self.median = self.samples[0]
                self.trimmed_mean = self.samples[0]
            return
        
        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)
        
        # Median (robust to outliers)
        self.median = statistics.median(sorted_samples)
        
        # Percentiles
        self.percentile_90 = float(np.percentile(sorted_samples, 90))
        self.percentile_95 = float(np.percentile(sorted_samples, 95))
        
        # IQR (Interquartile Range)
        q1 = float(np.percentile(sorted_samples, 25))
        q3 = float(np.percentile(sorted_samples, 75))
        self.iqr = q3 - q1
        
        # Trimmed mean (remove top and bottom 10%)
        trim_count = max(1, n // 10)
        trimmed = sorted_samples[trim_count:-trim_count] if n > 4 else sorted_samples
        self.trimmed_mean = statistics.mean(trimmed)
        
        # Standard deviation
        self.std_dev = statistics.stdev(sorted_samples) if n > 1 else 0
        
        # Coefficient of variation (lower = more consistent)
        mean_val = statistics.mean(sorted_samples)
        self.coefficient_of_variation = (self.std_dev / mean_val) if mean_val > 0 else 0
        
        # Confidence score (based on sample size and consistency)
        sample_factor = min(1.0, n / 5)  # Max out at 5 samples
        consistency_factor = max(0, 1 - self.coefficient_of_variation)
        self.confidence_score = round(sample_factor * consistency_factor, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'load_time_median': self.median,
            'load_time_trimmed_mean': self.trimmed_mean,
            'load_time_p90': self.percentile_90,
            'load_time_p95': self.percentile_95,
            'load_time_std_dev': self.std_dev,
            'load_time_iqr': self.iqr,
            'load_time_cv': self.coefficient_of_variation,
            'load_time_confidence': self.confidence_score,
            'load_time_samples': len(self.samples),
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary for reports."""
        if not self.samples:
            return "No load time data available."
        
        return (
            f"Load Time Analysis (n={len(self.samples)} samples):\n"
            f"  - Median: {self.median:.3f}s\n"
            f"  - Trimmed Mean: {self.trimmed_mean:.3f}s\n"
            f"  - 90th Percentile: {self.percentile_90:.3f}s\n"
            f"  - 95th Percentile: {self.percentile_95:.3f}s\n"
            f"  - Standard Deviation: {self.std_dev:.3f}s\n"
            f"  - Coefficient of Variation: {self.coefficient_of_variation:.2%}\n"
            f"  - Confidence Score: {self.confidence_score:.2f}/1.00"
        )