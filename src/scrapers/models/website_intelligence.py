"""Main data model for comprehensive website intelligence."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time

from ..metrics import (
    PerformanceMetrics,
    SEOMetrics,
    SecurityMetrics,
    AccessibilityMetrics,
    BusinessSignals,
)


@dataclass 
class WebsiteIntelligence:
    """Comprehensive data structure for website analysis results."""
    
    domain: str
    
    # Basic info
    status_code: int = 0
    final_url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    
    # CMS & Technology
    cms_detected: Optional[str] = None
    cms_version: Optional[str] = None
    is_outdated_cms: bool = False
    technologies: List[str] = field(default_factory=list)
    
    # Comprehensive metrics
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    seo: SEOMetrics = field(default_factory=SEOMetrics)
    security: SecurityMetrics = field(default_factory=SecurityMetrics)
    accessibility: AccessibilityMetrics = field(default_factory=AccessibilityMetrics)
    business: BusinessSignals = field(default_factory=BusinessSignals)
    
    # Mobile
    is_mobile_friendly: bool = True
    has_viewport_meta: bool = False
    
    # Overall scores
    overall_score: int = 0
    buyer_priority_score: int = 0  # How good a lead is this?
    
    # Meta
    analysis_timestamp: str = ""
    error: Optional[str] = None
    
    def calculate_overall_scores(self) -> None:
        """Calculate aggregate scores."""
        # Calculate component scores
        self.performance.calculate_grade()
        self.seo.calculate_score()
        self.security.calculate_score()
        self.accessibility.calculate_score()
        self.business.calculate_score()
        
        # Overall score (weighted)
        self.overall_score = int(
            self.performance.get_numeric_score() * 0.25 +
            self.seo.seo_score * 0.20 +
            self.security.security_headers_score * 0.20 +
            self.accessibility.accessibility_score * 0.15 +
            self.business.business_legitimacy_score * 0.20
        )
        
        # Buyer priority score (focuses on what matters for sales)
        self._calculate_buyer_priority()
    
    def _calculate_buyer_priority(self) -> None:
        """
        Calculate buyer priority score.
        
        Higher score = better lead (more issues to fix, but legitimate business)
        """
        issues_score = 0
        
        # Performance issues (opportunity to sell optimization)
        load_time = self.performance.load_time_metrics.trimmed_mean
        if load_time > 3:
            issues_score += 20
        elif load_time > 2:
            issues_score += 10
        
        # Security issues (opportunity to sell security)
        if not self.security.has_ssl:
            issues_score += 25
        if self.security.security_headers_score < 50:
            issues_score += 15
        
        # SEO issues (opportunity to sell SEO services)
        if self.seo.seo_score < 50:
            issues_score += 20
        
        # Outdated CMS (opportunity to sell redesign)
        if self.is_outdated_cms:
            issues_score += 25
        
        # But only if it's a legitimate business
        legitimacy_multiplier = self.business.business_legitimacy_score / 100
        
        self.buyer_priority_score = int(issues_score * legitimacy_multiplier)
    
    def to_flat_dict(self) -> Dict[str, Any]:
        """Flatten nested structure to flat dictionary for CSV export."""
        flat = {
            'domain': self.domain,
            'status_code': self.status_code,
            'final_url': self.final_url,
            'title': self.title,
            'meta_description': self.meta_description,
            'cms_detected': self.cms_detected,
            'cms_version': self.cms_version,
            'is_outdated_cms': self.is_outdated_cms,
            'technologies': ','.join(self.technologies),
            'is_mobile_friendly': self.is_mobile_friendly,
            'has_viewport_meta': self.has_viewport_meta,
            'overall_score': self.overall_score,
            'buyer_priority_score': self.buyer_priority_score,
            'error': self.error,
            'analysis_timestamp': self.analysis_timestamp,
        }
        
        # Add metrics from each component
        flat.update(self.performance.to_dict())
        flat.update(self.seo.to_dict())
        flat.update(self.security.to_dict())
        flat.update(self.accessibility.to_dict())
        flat.update(self.business.to_dict())
        
        return flat
    
    def get_all_issues(self) -> Dict[str, List[str]]:
        """Get all issues categorized by type."""
        return {
            'seo': self.seo.get_issues(),
            'security': self.security.get_issues(),
            'accessibility': self.accessibility.get_issues(),
            'business': self.business.get_missing_signals(),
        }
    
    def get_all_recommendations(self) -> Dict[str, List[str]]:
        """Get all recommendations categorized by type."""
        return {
            'seo': self.seo.get_recommendations(),
            'security': self.security.get_recommendations(),
            'accessibility': self.accessibility.get_recommendations(),
        }
    
    def get_executive_summary(self) -> str:
        """Get executive summary suitable for reports."""
        summary = (
            f"Website Analysis Report: {self.domain}\n"
            f"{'=' * 50}\n\n"
            f"Analysis Date: {self.analysis_timestamp}\n"
            f"Final URL: {self.final_url or 'N/A'}\n"
            f"Status: {'✓ Online' if self.status_code == 200 else f'⚠ Status {self.status_code}'}\n\n"
            
            f"OVERALL SCORES\n"
            f"{'-' * 30}\n"
            f"Overall Website Score: {self.overall_score}/100\n"
            f"Buyer Priority Score: {self.buyer_priority_score}\n"
            f"Lead Quality: {self.business.get_lead_quality()}\n\n"
            
            f"COMPONENT SCORES\n"
            f"{'-' * 30}\n"
            f"Performance: {self.performance.performance_grade} ({self.performance.get_numeric_score()}/100)\n"
            f"SEO: {self.seo.seo_score}/100\n"
            f"Security: {self.security.security_headers_score}/100 ({self.security.get_grade()})\n"
            f"Accessibility: {self.accessibility.accessibility_score}/100 ({self.accessibility.get_grade()})\n"
            f"Business Legitimacy: {self.business.business_legitimacy_score}/100\n\n"
        )
        
        if self.cms_detected:
            summary += f"CMS: {self.cms_detected}"
            if self.cms_version:
                summary += f" v{self.cms_version}"
            if self.is_outdated_cms:
                summary += " (OUTDATED)"
            summary += "\n"
        
        if self.technologies:
            summary += f"Technologies: {', '.join(self.technologies)}\n"
        
        return summary
    
    def get_full_report(self) -> str:
        """Get full detailed report."""
        report = self.get_executive_summary()
        
        report += f"\n{'=' * 50}\n"
        report += "DETAILED ANALYSIS\n"
        report += f"{'=' * 50}\n\n"
        
        report += self.performance.get_summary() + "\n"
        report += "-" * 40 + "\n\n"
        
        report += self.seo.get_summary() + "\n"
        report += "-" * 40 + "\n\n"
        
        report += self.security.get_summary() + "\n"
        report += "-" * 40 + "\n\n"
        
        report += self.accessibility.get_summary() + "\n"
        report += "-" * 40 + "\n\n"
        
        report += self.business.get_summary() + "\n"
        
        return report