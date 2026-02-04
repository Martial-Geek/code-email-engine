"""Accessibility metrics for website analysis."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class AccessibilityMetrics:
    """Basic accessibility metrics."""
    
    has_lang_attribute: bool = False
    has_skip_link: bool = False
    forms_have_labels: bool = True
    images_have_alt: bool = True
    has_aria_landmarks: bool = False
    color_contrast_issues: int = 0  # Would need browser automation
    accessibility_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate basic accessibility score."""
        score = 0
        if self.has_lang_attribute:
            score += 20
        if self.has_skip_link:
            score += 15
        if self.forms_have_labels:
            score += 20
        if self.images_have_alt:
            score += 25
        if self.has_aria_landmarks:
            score += 20
        
        self.accessibility_score = score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'accessibility_score': self.accessibility_score,
            'has_lang_attribute': self.has_lang_attribute,
            'has_skip_link': self.has_skip_link,
            'forms_have_labels': self.forms_have_labels,
            'images_have_alt': self.images_have_alt,
            'has_aria_landmarks': self.has_aria_landmarks,
            'color_contrast_issues': self.color_contrast_issues,
        }
    
    def get_issues(self) -> List[str]:
        """Get list of accessibility issues found."""
        issues = []
        
        if not self.has_lang_attribute:
            issues.append("Missing lang attribute on <html> element")
        if not self.has_skip_link:
            issues.append("No skip navigation link found")
        if not self.forms_have_labels:
            issues.append("Form inputs missing associated labels")
        if not self.images_have_alt:
            issues.append("Images missing alt attributes")
        if not self.has_aria_landmarks:
            issues.append("No ARIA landmarks found")
        if self.color_contrast_issues > 0:
            issues.append(f"{self.color_contrast_issues} color contrast issues")
        
        return issues
    
    def get_recommendations(self) -> List[str]:
        """Get accessibility improvement recommendations."""
        recommendations = []
        
        if not self.has_lang_attribute:
            recommendations.append(
                "Add a lang attribute to the <html> element to specify "
                "the page language (e.g., <html lang=\"en\">)."
            )
        if not self.has_skip_link:
            recommendations.append(
                "Add a 'Skip to main content' link at the beginning of "
                "the page for keyboard navigation users."
            )
        if not self.forms_have_labels:
            recommendations.append(
                "Ensure all form inputs have associated <label> elements "
                "or aria-label attributes."
            )
        if not self.images_have_alt:
            recommendations.append(
                "Add descriptive alt text to all images. Use empty alt=\"\" "
                "for decorative images."
            )
        if not self.has_aria_landmarks:
            recommendations.append(
                "Add ARIA landmark roles (main, navigation, banner, etc.) "
                "to help screen reader users navigate."
            )
        
        return recommendations
    
    def get_grade(self) -> str:
        """Get letter grade for accessibility."""
        score = self.accessibility_score
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        elif score >= 20:
            return "D"
        else:
            return "F"
    
    def get_summary(self) -> str:
        """Get human-readable summary for reports."""
        issues = self.get_issues()
        
        summary = (
            f"Accessibility Analysis:\n"
            f"  - Score: {self.accessibility_score}/100\n"
            f"  - Grade: {self.get_grade()}\n"
            f"  - Language Attribute: {'✓' if self.has_lang_attribute else '✗'}\n"
            f"  - Skip Navigation Link: {'✓' if self.has_skip_link else '✗'}\n"
            f"  - Form Labels: {'✓' if self.forms_have_labels else '✗'}\n"
            f"  - Image Alt Text: {'✓' if self.images_have_alt else '✗'}\n"
            f"  - ARIA Landmarks: {'✓' if self.has_aria_landmarks else '✗'}\n"
        )
        
        if issues:
            summary += f"\nIssues Found ({len(issues)}):\n"
            for issue in issues:
                summary += f"  • {issue}\n"
        
        return summary