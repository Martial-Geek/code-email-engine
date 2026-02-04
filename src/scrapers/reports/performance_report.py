"""Performance-focused report generator."""

from pathlib import Path
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from .base_report import BaseReport

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class PerformanceReport(BaseReport):
    """Generates performance-focused reports for website intelligence."""
    
    REPORT_TYPE = "performance"
    
    # Performance thresholds
    LOAD_TIME_EXCELLENT = 1.0
    LOAD_TIME_GOOD = 2.0
    LOAD_TIME_MODERATE = 3.0
    
    HTML_SIZE_GOOD = 100000  # 100KB
    HTML_SIZE_MODERATE = 300000  # 300KB
    
    CV_EXCELLENT = 0.1
    CV_GOOD = 0.25
    
    def generate(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate performance report as PDF.
        
        Args:
            intel: WebsiteIntelligence object
            filename: Output filename
            
        Returns:
            Path to the generated report
        """
        if not self._reportlab_available:
            return self.save_text_report(intel, filename)
        
        if filename is None:
            filename = self._generate_filename(intel, 'pdf')
        
        output_path = self.output_dir / filename
        self._generate_pdf(intel, output_path)
        
        return output_path
    
    def get_text_content(self, intel: 'WebsiteIntelligence') -> str:
        """Get performance report as plain text."""
        perf = intel.performance
        load_time = perf.load_time_metrics
        
        content = self._format_header(f"PERFORMANCE ANALYSIS REPORT: {intel.domain}")
        content += f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"URL: {intel.final_url or intel.domain}\n"
        
        # Overall Grade
        content += self._format_subheader("OVERALL PERFORMANCE GRADE")
        content += f"Grade: {perf.performance_grade}\n"
        content += f"Score: {perf.get_numeric_score()}/100\n"
        
        # Load Time Statistics
        content += self._format_subheader("LOAD TIME STATISTICS")
        if load_time.samples:
            content += f"  Number of Measurements: {len(load_time.samples)}\n"
            content += f"  Median Load Time: {load_time.median:.3f}s\n"
            content += f"  Trimmed Mean: {load_time.trimmed_mean:.3f}s\n"
            content += f"  90th Percentile: {load_time.percentile_90:.3f}s\n"
            content += f"  95th Percentile: {load_time.percentile_95:.3f}s\n"
            content += f"  Standard Deviation: {load_time.std_dev:.3f}s\n"
            content += f"  Coefficient of Variation: {load_time.coefficient_of_variation:.2%}\n"
            content += f"  Confidence Score: {load_time.confidence_score:.2f}/1.00\n"
            content += f"\n  Raw Samples: {load_time.samples}\n"
        else:
            content += "  No load time data available.\n"
        
        # Size Metrics
        content += self._format_subheader("SIZE METRICS")
        content += f"  HTML Size: {perf.html_size_bytes:,} bytes ({perf.html_size_bytes/1024:.1f} KB)\n"
        
        size_rating = self._get_size_rating(perf.html_size_bytes)
        content += f"  Size Rating: {size_rating}\n"
        
        # Timing Breakdown (if available)
        if perf.ttfb > 0:
            content += self._format_subheader("TIMING BREAKDOWN")
            content += f"  DNS Lookup: {perf.dns_lookup_time:.3f}s\n"
            content += f"  TCP Connect: {perf.tcp_connect_time:.3f}s\n"
            content += f"  Time to First Byte (TTFB): {perf.ttfb:.3f}s\n"
            content += f"  DOM Content Loaded: {perf.dom_content_loaded:.3f}s\n"
            content += f"  Fully Loaded: {perf.fully_loaded:.3f}s\n"
        
        # Performance Analysis
        content += self._format_subheader("PERFORMANCE ANALYSIS")
        analysis = self._get_performance_analysis(intel)
        for item in analysis:
            content += f"  {item}\n"
        
        # Recommendations
        content += self._format_subheader("RECOMMENDATIONS")
        recommendations = self.get_recommendations(intel)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                content += f"  {i}. {rec}\n"
        else:
            content += "  No major issues found.\n"
        
        return content
    
    def _get_size_rating(self, size_bytes: int) -> str:
        """Get rating for HTML size."""
        if size_bytes < self.HTML_SIZE_GOOD:
            return "Good"
        elif size_bytes < self.HTML_SIZE_MODERATE:
            return "Moderate"
        else:
            return "Large"
    
    def _get_performance_analysis(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Get performance analysis items."""
        analysis = []
        perf = intel.performance
        load_time = perf.load_time_metrics
        
        # Load time assessment
        if load_time.median > 0:
            if load_time.median < self.LOAD_TIME_EXCELLENT:
                analysis.append("✓ Excellent load time (< 1 second)")
            elif load_time.median < self.LOAD_TIME_GOOD:
                analysis.append("✓ Good load time (< 2 seconds)")
            elif load_time.median < self.LOAD_TIME_MODERATE:
                analysis.append("⚠ Moderate load time (< 3 seconds)")
            else:
                analysis.append("✗ Slow load time (> 3 seconds)")
        
        # Consistency assessment
        if load_time.coefficient_of_variation > 0:
            if load_time.coefficient_of_variation < self.CV_EXCELLENT:
                analysis.append("✓ Very consistent performance")
            elif load_time.coefficient_of_variation < self.CV_GOOD:
                analysis.append("✓ Consistent performance")
            else:
                analysis.append("⚠ Variable performance (high CV)")
        
        # Size assessment
        if perf.html_size_bytes < self.HTML_SIZE_GOOD:
            analysis.append("✓ HTML size is optimized")
        elif perf.html_size_bytes < self.HTML_SIZE_MODERATE:
            analysis.append("⚠ HTML size is moderate")
        else:
            analysis.append("✗ HTML size is large - consider optimization")
        
        # TTFB assessment
        if perf.ttfb > 0:
            if perf.ttfb < 0.2:
                analysis.append("✓ Excellent TTFB (< 200ms)")
            elif perf.ttfb < 0.5:
                analysis.append("✓ Good TTFB (< 500ms)")
            elif perf.ttfb < 1.0:
                analysis.append("⚠ Moderate TTFB (< 1s)")
            else:
                analysis.append("✗ Slow TTFB (> 1s)")
        
        # Confidence assessment
        if load_time.confidence_score > 0:
            if load_time.confidence_score >= 0.8:
                analysis.append("✓ High measurement confidence")
            elif load_time.confidence_score >= 0.5:
                analysis.append("⚠ Moderate measurement confidence")
            else:
                analysis.append("⚠ Low measurement confidence - results may vary")
        
        return analysis
    
    def get_recommendations(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Get performance improvement recommendations."""
        recommendations = []
        perf = intel.performance
        load_time = perf.load_time_metrics
        
        if load_time.median > self.LOAD_TIME_MODERATE:
            recommendations.append(
                "Critical: Load time exceeds 3 seconds. Consider server optimization, "
                "caching, CDN implementation, or reducing page weight."
            )
        elif load_time.median > self.LOAD_TIME_GOOD:
            recommendations.append(
                "Load time is moderate. Consider implementing browser caching "
                "and optimizing images to improve performance."
            )
        
        if perf.html_size_bytes > self.HTML_SIZE_MODERATE:
            recommendations.append(
                "HTML size is large (>300KB). Consider minifying HTML, "
                "removing unnecessary code, and lazy loading content."
            )
        elif perf.html_size_bytes > self.HTML_SIZE_GOOD:
            recommendations.append(
                "HTML size is moderate. Consider minification and removing "
                "unnecessary whitespace and comments."
            )
        
        if load_time.coefficient_of_variation > self.CV_GOOD:
            recommendations.append(
                "Performance is inconsistent. This may indicate server issues, "
                "network problems, or resource contention. Consider load balancing."
            )
        
        if perf.ttfb > 1.0:
            recommendations.append(
                "Time to First Byte is slow. Consider server-side caching, "
                "database optimization, or upgrading hosting infrastructure."
            )
        
        if not intel.security.has_ssl:
            recommendations.append(
                "Enable HTTPS - modern browsers prioritize secure connections "
                "and may perform optimizations for HTTPS sites."
            )
        
        # Check for technologies that might affect performance
        if 'jquery' in intel.technologies and 'react' in intel.technologies:
            recommendations.append(
                "Multiple JavaScript frameworks detected. Consider consolidating "
                "to reduce bundle size and improve load times."
            )
        
        if not intel.has_viewport_meta:
            recommendations.append(
                "Missing viewport meta tag. Add it to ensure proper rendering "
                "on mobile devices and improve perceived performance."
            )
        
        return recommendations
    
    def _generate_pdf(self, intel: 'WebsiteIntelligence', output_path: Path) -> None:
        """Generate PDF version of performance report."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#1a1a2e')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=HexColor('#16213e')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        perf = intel.performance
        load_time = perf.load_time_metrics
        story = []
        
        # Title
        story.append(Paragraph("Performance Analysis Report", title_style))
        story.append(Paragraph(
            f"<b>{intel.domain}</b>",
            ParagraphStyle('Domain', parent=styles['Heading3'], 
                          alignment=TA_CENTER, textColor=HexColor('#e94560'))
        ))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 20))
        
        # Overall Grade
        story.append(Paragraph("Overall Performance Grade", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        grade_colors = {
            'A': '#27ae60',
            'B': '#2ecc71',
            'C': '#f39c12',
            'D': '#e67e22',
            'F': '#e74c3c',
            'unknown': '#95a5a6'
        }
        grade_color = HexColor(grade_colors.get(perf.performance_grade, '#95a5a6'))
        
        story.append(Paragraph(
            f"<font size='36' color='{grade_color.hexval()}'><b>{perf.performance_grade}</b></font>",
            ParagraphStyle('Grade', parent=styles['Normal'], alignment=TA_CENTER, spaceBefore=15)
        ))
        story.append(Paragraph(
            f"Score: {perf.get_numeric_score()}/100",
            ParagraphStyle('Score', parent=styles['Normal'], alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 20))
        
        # Load Time Statistics Table
        story.append(Paragraph("Load Time Statistics", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        if load_time.samples:
            stats_data = [
                ['Metric', 'Value', 'Description'],
                ['Samples', str(len(load_time.samples)), 'Number of measurements'],
                ['Median', f'{load_time.median:.3f}s', 'Middle value (robust)'],
                ['Trimmed Mean', f'{load_time.trimmed_mean:.3f}s', 'Mean without outliers'],
                ['90th Percentile', f'{load_time.percentile_90:.3f}s', '90% of loads faster'],
                ['95th Percentile', f'{load_time.percentile_95:.3f}s', '95% of loads faster'],
                ['Std Deviation', f'{load_time.std_dev:.3f}s', 'Variation measure'],
                ['CV', f'{load_time.coefficient_of_variation:.2%}', 'Consistency measure'],
                ['Confidence', f'{load_time.confidence_score:.0%}', 'Measurement reliability'],
            ]
            
            stats_table = Table(stats_data, colWidths=[1.8*inch, 1.2*inch, 2.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
            ]))
            story.append(stats_table)
        else:
            story.append(Paragraph("No load time data available.", normal_style))
        
        story.append(Spacer(1, 20))
        
        # Size Metrics
        story.append(Paragraph("Size Metrics", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        size_kb = perf.html_size_bytes / 1024
        size_rating = self._get_size_rating(perf.html_size_bytes)
        
        size_data = [
            ['Metric', 'Value'],
            ['HTML Size (bytes)', f'{perf.html_size_bytes:,}'],
            ['HTML Size (KB)', f'{size_kb:.1f}'],
            ['Size Rating', size_rating],
        ]
        
        size_table = Table(size_data, colWidths=[2.5*inch, 2.5*inch])
        size_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(size_table)
        story.append(Spacer(1, 20))
        
        # Performance Analysis
        story.append(Paragraph("Performance Analysis", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        analysis = self._get_performance_analysis(intel)
        for item in analysis:
            story.append(Paragraph(item, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Recommendations
        recommendations = self.get_recommendations(intel)
        if recommendations:
            story.append(Paragraph("Recommendations", heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
            
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"<b>{i}.</b> {rec}", normal_style))
        
        doc.build(story)
    
    def get_load_time_summary(self, intel: 'WebsiteIntelligence') -> dict:
        """Get a summary dictionary of load time metrics."""
        load_time = intel.performance.load_time_metrics
        
        return {
            'samples': len(load_time.samples),
            'median': load_time.median,
            'trimmed_mean': load_time.trimmed_mean,
            'p90': load_time.percentile_90,
            'p95': load_time.percentile_95,
            'std_dev': load_time.std_dev,
            'cv': load_time.coefficient_of_variation,
            'confidence': load_time.confidence_score,
            'grade': intel.performance.performance_grade,
        }