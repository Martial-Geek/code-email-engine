"""Business signals for website analysis."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class BusinessSignals:
    """Business-related signals for buyer qualification."""
    
    has_contact_page: bool = False
    has_contact_form: bool = False
    has_phone_number: bool = False
    has_email: bool = False
    has_physical_address: bool = False
    has_social_links: bool = False
    social_platforms: List[str] = field(default_factory=list)
    has_blog: bool = False
    has_testimonials: bool = False
    has_pricing_page: bool = False
    has_about_page: bool = False
    has_privacy_policy: bool = False
    has_terms_of_service: bool = False
    copyright_year: Optional[int] = None
    estimated_company_size: Optional[str] = None  # Based on signals
    business_legitimacy_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate business legitimacy score."""
        score = 0
        
        if self.has_contact_page:
            score += 10
        if self.has_contact_form:
            score += 5
        if self.has_phone_number:
            score += 15
        if self.has_email:
            score += 10
        if self.has_physical_address:
            score += 15
        if self.has_social_links:
            score += 5
        if len(self.social_platforms) >= 3:
            score += 5
        if self.has_about_page:
            score += 10
        if self.has_privacy_policy:
            score += 10
        if self.has_terms_of_service:
            score += 5
        if self.copyright_year and self.copyright_year >= 2023:
            score += 10
        
        self.business_legitimacy_score = min(100, score)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'business_legitimacy_score': self.business_legitimacy_score,
            'has_contact_page': self.has_contact_page,
            'has_contact_form': self.has_contact_form,
            'has_phone_number': self.has_phone_number,
            'has_email': self.has_email,
            'has_physical_address': self.has_physical_address,
            'has_social_links': self.has_social_links,
            'social_platforms': ','.join(self.social_platforms),
            'social_platforms_count': len(self.social_platforms),
            'has_blog': self.has_blog,
            'has_testimonials': self.has_testimonials,
            'has_pricing_page': self.has_pricing_page,
            'has_about_page': self.has_about_page,
            'has_privacy_policy': self.has_privacy_policy,
            'has_terms_of_service': self.has_terms_of_service,
            'copyright_year': self.copyright_year,
            'estimated_company_size': self.estimated_company_size,
        }
    
    def get_positive_signals(self) -> List[str]:
        """Get list of positive business signals."""
        signals = []
        
        if self.has_contact_page:
            signals.append("Has dedicated contact page")
        if self.has_contact_form:
            signals.append("Has contact form")
        if self.has_phone_number:
            signals.append("Phone number visible")
        if self.has_email:
            signals.append("Email address visible")
        if self.has_physical_address:
            signals.append("Physical address present")
        if self.has_about_page:
            signals.append("Has about page")
        if self.has_privacy_policy:
            signals.append("Has privacy policy")
        if self.has_terms_of_service:
            signals.append("Has terms of service")
        if self.has_blog:
            signals.append("Active blog/content")
        if self.has_testimonials:
            signals.append("Customer testimonials present")
        if len(self.social_platforms) > 0:
            signals.append(f"Social presence: {', '.join(self.social_platforms)}")
        
        return signals
    
    def get_missing_signals(self) -> List[str]:
        """Get list of missing business signals."""
        missing = []
        
        if not self.has_phone_number:
            missing.append("No phone number")
        if not self.has_physical_address:
            missing.append("No physical address")
        if not self.has_privacy_policy:
            missing.append("Missing privacy policy")
        if not self.has_about_page:
            missing.append("No about page")
        if not self.has_social_links:
            missing.append("No social media links")
        
        return missing
    
    def get_lead_quality(self) -> str:
        """Assess lead quality based on business signals."""
        score = self.business_legitimacy_score
        
        if score >= 80:
            return "High Quality - Established Business"
        elif score >= 60:
            return "Good Quality - Legitimate Business"
        elif score >= 40:
            return "Medium Quality - Basic Presence"
        elif score >= 20:
            return "Low Quality - Limited Information"
        else:
            return "Poor Quality - Minimal Business Signals"
    
    def get_summary(self) -> str:
        """Get human-readable summary for reports."""
        positive = self.get_positive_signals()
        missing = self.get_missing_signals()
        
        summary = (
            f"Business Analysis:\n"
            f"  - Legitimacy Score: {self.business_legitimacy_score}/100\n"
            f"  - Lead Quality: {self.get_lead_quality()}\n"
            f"  - Contact Page: {'✓' if self.has_contact_page else '✗'}\n"
            f"  - Phone Number: {'✓' if self.has_phone_number else '✗'}\n"
            f"  - Email: {'✓' if self.has_email else '✗'}\n"
            f"  - Physical Address: {'✓' if self.has_physical_address else '✗'}\n"
            f"  - About Page: {'✓' if self.has_about_page else '✗'}\n"
            f"  - Privacy Policy: {'✓' if self.has_privacy_policy else '✗'}\n"
            f"  - Social Platforms: {len(self.social_platforms)}\n"
        )
        
        if self.copyright_year:
            summary += f"  - Copyright Year: {self.copyright_year}\n"
        
        if missing:
            summary += f"\nMissing Signals:\n"
            for item in missing:
                summary += f"  • {item}\n"
        
        return summary