"""SEO metrics for website analysis."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SEOMetrics:
    """SEO-related metrics for buyer perspective."""
    
    has_meta_description: bool = False
    has_meta_keywords: bool = False
    has_og_tags: bool = False  # Open Graph
    has_twitter_cards: bool = False
    has_structured_data: bool = False  # JSON-LD, microdata
    has_sitemap: bool = False
    has_robots_txt: bool = False
    canonical_url: Optional[str] = None
    h1_count: int = 0
    h2_count: int = 0
    image_count: int = 0
    images_without_alt: int = 0
    internal_links: int = 0
    external_links: int = 0
    seo_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate overall SEO score."""
        score = 0
        
        if self.has_meta_description:
            score += 15
        if self.has_og_tags:
            score += 10
        if self.has_twitter_cards:
            score += 5
        if self.has_structured_data:
            score += 15
        if self.has_sitemap:
            score += 10
        if self.has_robots_txt:
            score += 5
        if self.h1_count == 1:  # Exactly one H1 is best practice
            score += 10
        if self.h2_count > 0:
            score += 5
        if self.images_without_alt == 0 and self.image_count > 0:
            score += 10
        elif self.image_count > 0:
            alt_ratio = 1 - (self.images_without_alt / self.image_count)
            score += int(10 * alt_ratio)
        if self.canonical_url:
            score += 5
        
        # Penalize issues
        if self.h1_count > 1:
            score -= 5
        if self.h1_count == 0:
            score -= 10
        
        self.seo_score = max(0, min(100, score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'seo_score': self.seo_score,
            'has_meta_description': self.has_meta_description,
            'has_meta_keywords': self.has_meta_keywords,
            'has_og_tags': self.has_og_tags,
            'has_twitter_cards': self.has_twitter_cards,
            'has_structured_data': self.has_structured_data,
            'has_sitemap': self.has_sitemap,
            'has_robots_txt': self.has_robots_txt,
            'canonical_url': self.canonical_url,
            'h1_count': self.h1_count,
            'h2_count': self.h2_count,
            'image_count': self.image_count,
            'images_without_alt': self.images_without_alt,
            'internal_links': self.internal_links,
            'external_links': self.external_links,
        }
    
    def get_issues(self) -> List[str]:
        """Get list of SEO issues found."""
        issues = []
        
        if not self.has_meta_description:
            issues.append("Missing meta description")
        if not self.has_og_tags:
            issues.append("Missing Open Graph tags")
        if not self.has_structured_data:
            issues.append("No structured data (JSON-LD/microdata)")
        if not self.has_sitemap:
            issues.append("Missing sitemap.xml")
        if not self.has_robots_txt:
            issues.append("Missing robots.txt")
        if self.h1_count == 0:
            issues.append("No H1 heading found")
        if self.h1_count > 1:
            issues.append(f"Multiple H1 headings ({self.h1_count})")
        if self.images_without_alt > 0:
            issues.append(f"{self.images_without_alt} images missing alt text")
        if not self.canonical_url:
            issues.append("Missing canonical URL")
        
        return issues
    
    def get_recommendations(self) -> List[str]:
        """Get SEO improvement recommendations."""
        recommendations = []
        
        if not self.has_meta_description:
            recommendations.append(
                "Add a compelling meta description (150-160 characters) "
                "to improve click-through rates from search results."
            )
        if not self.has_og_tags:
            recommendations.append(
                "Add Open Graph meta tags for better social media sharing."
            )
        if not self.has_structured_data:
            recommendations.append(
                "Implement JSON-LD structured data to help search engines "
                "understand your content and enable rich snippets."
            )
        if not self.has_sitemap:
            recommendations.append(
                "Create and submit a sitemap.xml to help search engines "
                "discover all your pages."
            )
        if self.h1_count != 1:
            recommendations.append(
                "Ensure each page has exactly one H1 heading that describes "
                "the main topic of the page."
            )
        if self.images_without_alt > 0:
            recommendations.append(
                f"Add descriptive alt text to {self.images_without_alt} images "
                "for accessibility and image SEO."
            )
        
        return recommendations
    
    def get_summary(self) -> str:
        """Get human-readable summary for reports."""
        issues = self.get_issues()
        
        summary = (
            f"SEO Analysis:\n"
            f"  - Score: {self.seo_score}/100\n"
            f"  - Meta Description: {'✓' if self.has_meta_description else '✗'}\n"
            f"  - Open Graph Tags: {'✓' if self.has_og_tags else '✗'}\n"
            f"  - Twitter Cards: {'✓' if self.has_twitter_cards else '✗'}\n"
            f"  - Structured Data: {'✓' if self.has_structured_data else '✗'}\n"
            f"  - Sitemap: {'✓' if self.has_sitemap else '✗'}\n"
            f"  - Robots.txt: {'✓' if self.has_robots_txt else '✗'}\n"
            f"  - H1 Count: {self.h1_count}\n"
            f"  - H2 Count: {self.h2_count}\n"
            f"  - Images: {self.image_count} total, {self.images_without_alt} missing alt\n"
            f"  - Links: {self.internal_links} internal, {self.external_links} external\n"
        )
        
        if issues:
            summary += f"\nIssues Found ({len(issues)}):\n"
            for issue in issues:
                summary += f"  • {issue}\n"
        
        return summary