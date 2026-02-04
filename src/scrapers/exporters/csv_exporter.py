"""CSV exporter for website intelligence data."""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.website_intelligence import WebsiteIntelligence


class CSVExporter:
    """Exports website intelligence data to CSV format."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize CSV exporter.
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = output_dir or Path("data/enriched")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        results: List[WebsiteIntelligence],
        filename: Optional[str] = None,
        include_all_fields: bool = True
    ) -> Path:
        """
        Export website intelligence results to CSV.
        
        Args:
            results: List of WebsiteIntelligence objects
            filename: Output filename (auto-generated if not provided)
            include_all_fields: Whether to include all fields or just essential ones
            
        Returns:
            Path to the saved CSV file
        """
        if not results:
            raise ValueError("No results to export")
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"website_intelligence_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Convert results to flat dictionaries
        if include_all_fields:
            rows = [r.to_flat_dict() for r in results]
        else:
            rows = [self._get_essential_fields(r) for r in results]
        
        # Write CSV
        if rows:
            fieldnames = list(rows[0].keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return output_path
    
    def _get_essential_fields(self, intel: WebsiteIntelligence) -> Dict[str, Any]:
        """Get only essential fields for a compact export."""
        return {
            'domain': intel.domain,
            'status_code': intel.status_code,
            'final_url': intel.final_url,
            'title': intel.title,
            'cms_detected': intel.cms_detected,
            'is_outdated_cms': intel.is_outdated_cms,
            'overall_score': intel.overall_score,
            'buyer_priority_score': intel.buyer_priority_score,
            'performance_grade': intel.performance.performance_grade,
            'load_time_median': intel.performance.load_time_metrics.median,
            'seo_score': intel.seo.seo_score,
            'security_score': intel.security.security_headers_score,
            'has_ssl': intel.security.has_ssl,
            'accessibility_score': intel.accessibility.accessibility_score,
            'business_score': intel.business.business_legitimacy_score,
            'has_contact_form': intel.business.has_contact_form,
            'has_phone_number': intel.business.has_phone_number,
            'error': intel.error,
        }
    
    def export_summary(
        self,
        results: List[WebsiteIntelligence],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export a summary CSV with aggregated statistics.
        
        Args:
            results: List of WebsiteIntelligence objects
            filename: Output filename
            
        Returns:
            Path to the saved CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"website_intelligence_summary_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in summary.items():
                writer.writerow([key, value])
        
        return output_path
    
    def _calculate_summary(self, results: List[WebsiteIntelligence]) -> Dict[str, Any]:
        """Calculate summary statistics from results."""
        total = len(results)
        successful = len([r for r in results if r.error is None])
        
        # Filter successful results for statistics
        successful_results = [r for r in results if r.error is None]
        
        if not successful_results:
            return {
                'total_analyzed': total,
                'successful': 0,
                'failed': total,
            }
        
        # Calculate averages
        avg_overall = sum(r.overall_score for r in successful_results) / len(successful_results)
        avg_seo = sum(r.seo.seo_score for r in successful_results) / len(successful_results)
        avg_security = sum(r.security.security_headers_score for r in successful_results) / len(successful_results)
        avg_accessibility = sum(r.accessibility.accessibility_score for r in successful_results) / len(successful_results)
        avg_business = sum(r.business.business_legitimacy_score for r in successful_results) / len(successful_results)
        
        # Load time statistics
        load_times = [
            r.performance.load_time_metrics.median 
            for r in successful_results 
            if r.performance.load_time_metrics.median > 0
        ]
        avg_load_time = sum(load_times) / len(load_times) if load_times else 0
        
        # Counts
        with_ssl = len([r for r in successful_results if r.security.has_ssl])
        outdated_cms = len([r for r in successful_results if r.is_outdated_cms])
        high_priority = len([r for r in successful_results if r.buyer_priority_score >= 50])
        
        # CMS distribution
        cms_counts = {}
        for r in successful_results:
            if r.cms_detected:
                cms_counts[r.cms_detected] = cms_counts.get(r.cms_detected, 0) + 1
        
        top_cms = sorted(cms_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_analyzed': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': f"{(successful/total)*100:.1f}%",
            'avg_overall_score': round(avg_overall, 1),
            'avg_seo_score': round(avg_seo, 1),
            'avg_security_score': round(avg_security, 1),
            'avg_accessibility_score': round(avg_accessibility, 1),
            'avg_business_score': round(avg_business, 1),
            'avg_load_time_seconds': round(avg_load_time, 2),
            'sites_with_ssl': with_ssl,
            'ssl_percentage': f"{(with_ssl/successful)*100:.1f}%",
            'outdated_cms_count': outdated_cms,
            'high_priority_leads': high_priority,
            'top_cms': str(top_cms),
        }
    
    def export_by_score(
        self,
        results: List[WebsiteIntelligence],
        min_score: int = 0,
        max_score: int = 100,
        score_type: str = 'buyer_priority_score',
        filename: Optional[str] = None
    ) -> Path:
        """
        Export filtered results based on score range.
        
        Args:
            results: List of WebsiteIntelligence objects
            min_score: Minimum score to include
            max_score: Maximum score to include
            score_type: Which score to filter by
            filename: Output filename
            
        Returns:
            Path to the saved CSV file
        """
        # Filter results
        filtered = [
            r for r in results
            if min_score <= getattr(r, score_type, 0) <= max_score
        ]
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"filtered_{score_type}_{min_score}-{max_score}_{timestamp}.csv"
        
        return self.export(filtered, filename)