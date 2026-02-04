"""Security metrics for website analysis."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class SecurityMetrics:
    """Security-related metrics."""
    
    has_ssl: bool = False
    ssl_grade: Optional[str] = None  # Would need SSL Labs API
    has_hsts: bool = False
    has_csp: bool = False  # Content Security Policy
    has_x_frame_options: bool = False
    has_x_content_type_options: bool = False
    has_x_xss_protection: bool = False
    security_headers_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate security headers score."""
        score = 0
        if self.has_ssl:
            score += 30
        if self.has_hsts:
            score += 20
        if self.has_csp:
            score += 20
        if self.has_x_frame_options:
            score += 10
        if self.has_x_content_type_options:
            score += 10
        if self.has_x_xss_protection:
            score += 10
        
        self.security_headers_score = score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'has_ssl': self.has_ssl,
            'ssl_grade': self.ssl_grade,
            'has_hsts': self.has_hsts,
            'has_csp': self.has_csp,
            'has_x_frame_options': self.has_x_frame_options,
            'has_x_content_type_options': self.has_x_content_type_options,
            'has_x_xss_protection': self.has_x_xss_protection,
            'security_headers_score': self.security_headers_score,
        }
    
    def get_issues(self) -> List[str]:
        """Get list of security issues found."""
        issues = []
        
        if not self.has_ssl:
            issues.append("No SSL/HTTPS - CRITICAL")
        if not self.has_hsts:
            issues.append("Missing HSTS header")
        if not self.has_csp:
            issues.append("Missing Content Security Policy")
        if not self.has_x_frame_options:
            issues.append("Missing X-Frame-Options header")
        if not self.has_x_content_type_options:
            issues.append("Missing X-Content-Type-Options header")
        if not self.has_x_xss_protection:
            issues.append("Missing X-XSS-Protection header")
        
        return issues
    
    def get_recommendations(self) -> List[str]:
        """Get security improvement recommendations."""
        recommendations = []
        
        if not self.has_ssl:
            recommendations.append(
                "CRITICAL: Enable HTTPS with a valid SSL certificate. "
                "This is essential for security and SEO."
            )
        if not self.has_hsts:
            recommendations.append(
                "Add Strict-Transport-Security header to enforce HTTPS "
                "and prevent downgrade attacks."
            )
        if not self.has_csp:
            recommendations.append(
                "Implement Content-Security-Policy to prevent XSS attacks "
                "and control resource loading."
            )
        if not self.has_x_frame_options:
            recommendations.append(
                "Add X-Frame-Options header to prevent clickjacking attacks."
            )
        if not self.has_x_content_type_options:
            recommendations.append(
                "Add X-Content-Type-Options: nosniff to prevent MIME-type sniffing."
            )
        
        return recommendations
    
    def get_grade(self) -> str:
        """Get letter grade for security."""
        score = self.security_headers_score
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
    
    def get_summary(self) -> str:
        """Get human-readable summary for reports."""
        issues = self.get_issues()
        
        summary = (
            f"Security Analysis:\n"
            f"  - Score: {self.security_headers_score}/100\n"
            f"  - Grade: {self.get_grade()}\n"
            f"  - SSL/HTTPS: {'✓' if self.has_ssl else '✗ CRITICAL'}\n"
            f"  - HSTS: {'✓' if self.has_hsts else '✗'}\n"
            f"  - Content Security Policy: {'✓' if self.has_csp else '✗'}\n"
            f"  - X-Frame-Options: {'✓' if self.has_x_frame_options else '✗'}\n"
            f"  - X-Content-Type-Options: {'✓' if self.has_x_content_type_options else '✗'}\n"
            f"  - X-XSS-Protection: {'✓' if self.has_x_xss_protection else '✗'}\n"
        )
        
        if issues:
            summary += f"\nIssues Found ({len(issues)}):\n"
            for issue in issues:
                summary += f"  • {issue}\n"
        
        return summary