"""Performance metrics for website analysis."""

from dataclasses import dataclass, field
from typing import Dict, Any

from .load_time import LoadTimeMetrics


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    
    # Load time stats
    load_time_metrics: LoadTimeMetrics = field(default_factory=LoadTimeMetrics)
    
    # Size metrics
    html_size_bytes: int = 0
    total_requests: int = 0  # Would need browser automation
    
    # Timing breakdown (when using browser automation)
    dns_lookup_time: float = 0.0
    tcp_connect_time: float = 0.0
    ttfb: float = 0.0  # Time to First Byte
    dom_content_loaded: float = 0.0
    fully_loaded: float = 0.0
    
    # Derived metrics
    performance_grade: str = "unknown"  # A, B, C, D, F
    
    def calculate_grade(self) -> None:
        """Calculate performance grade based on metrics."""
        score = 100
        
        # Penalize slow load times (using trimmed mean)
        load_time = self.load_time_metrics.trimmed_mean or self.load_time_metrics.median
        if load_time > 5:
            score -= 40
        elif load_time > 3:
            score -= 25
        elif load_time > 2:
            score -= 10
        elif load_time > 1:
            score -= 5
        
        # Penalize large HTML
        if self.html_size_bytes > 500000:  # 500KB
            score -= 20
        elif self.html_size_bytes > 200000:  # 200KB
            score -= 10
        
        # Penalize slow TTFB
        if self.ttfb > 1:
            score -= 15
        elif self.ttfb > 0.5:
            score -= 5
        
        # Grade assignment
        if score >= 90:
            self.performance_grade = "A"
        elif score >= 80:
            self.performance_grade = "B"
        elif score >= 70:
            self.performance_grade = "C"
        elif score >= 60:
            self.performance_grade = "D"
        else:
            self.performance_grade = "F"
    
    def get_numeric_score(self) -> int:
        """Convert performance grade to numeric score."""
        grade_map = {"A": 100, "B": 85, "C": 70, "D": 55, "F": 40, "unknown": 50}
        return grade_map.get(self.performance_grade, 50)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        result = self.load_time_metrics.to_dict()
        result.update({
            'html_size_bytes': self.html_size_bytes,
            'total_requests': self.total_requests,
            'dns_lookup_time': self.dns_lookup_time,
            'tcp_connect_time': self.tcp_connect_time,
            'ttfb': self.ttfb,
            'dom_content_loaded': self.dom_content_loaded,
            'fully_loaded': self.fully_loaded,
            'performance_grade': self.performance_grade,
            'performance_score': self.get_numeric_score(),
        })
        return result
    
    def get_summary(self) -> str:
        """Get human-readable summary for reports."""
        html_size_kb = self.html_size_bytes / 1024
        
        summary = (
            f"Performance Analysis:\n"
            f"  - Grade: {self.performance_grade}\n"
            f"  - HTML Size: {html_size_kb:.1f} KB\n"
        )
        
        if self.ttfb > 0:
            summary += f"  - Time to First Byte: {self.ttfb:.3f}s\n"
        
        summary += f"\n{self.load_time_metrics.get_summary()}"
        
        return summary