"""Full comprehensive report generator combining all analysis areas."""

from pathlib import Path
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime

from .base_report import BaseReport
from .seo_report import SEOReport
from .performance_report import PerformanceReport
from .security_report import SecurityReport

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class FullReport(BaseReport):
    """
    Generates comprehensive reports combining all analysis areas.
    
    This report includes:
    - Executive Summary
    - Performance Analysis
    - SEO Analysis
    - Security Analysis
    - Accessibility Analysis
    - Business Signals
    - Recommendations
    """
    
    REPORT_TYPE = "full"
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize full report generator."""
        super().__init__(output_dir)
        
        # Initialize component reports for reuse
        self.seo_report = SEOReport(output_dir)
        self.performance_report = PerformanceReport(output_dir)
        self.security_report = SecurityReport(output_dir)
    
    def generate(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate full comprehensive report as PDF.
        
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
    
    def generate_all_reports(
        self,
        intel: 'WebsiteIntelligence',
        include_individual: bool = True
    ) -> Dict[str, Path]:
        """
        Generate full report and optionally individual reports.
        
        Args:
            intel: WebsiteIntelligence object
            include_individual: Whether to also generate individual reports
            
        Returns:
            Dictionary mapping report type to file path
        """
        reports = {}
        
        # Generate full report
        reports['full'] = self.generate(intel)
        
        if include_individual:
            reports['seo'] = self.seo_report.generate(intel)
            reports['performance'] = self.performance_report.generate(intel)
            reports['security'] = self.security_report.generate(intel)
        
        return reports
    
    def get_text_content(self, intel: 'WebsiteIntelligence') -> str:
        """Get full report as plain text."""
        content = self._format_header(f"COMPREHENSIVE WEBSITE ANALYSIS REPORT")
        content += f"\nDomain: {intel.domain}\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"URL: {intel.final_url or intel.domain}\n"
        
        # Executive Summary
        content += self._format_header("EXECUTIVE SUMMARY")
        content += self._get_executive_summary(intel)
        
        # Overall Scores
        content += self._format_subheader("OVERALL SCORES")
        content += f"  Overall Website Score: {intel.overall_score}/100\n"
        content += f"  Buyer Priority Score: {intel.buyer_priority_score}\n"
        content += f"  Lead Quality: {intel.business.get_lead_quality()}\n\n"
        
        content += "  Component Scores:\n"
        content += f"    Performance: {intel.performance.performance_grade} ({intel.performance.get_numeric_score()}/100)\n"
        content += f"    SEO: {intel.seo.seo_score}/100\n"
        content += f"    Security: {intel.security.security_headers_score}/100\n"
        content += f"    Accessibility: {intel.accessibility.accessibility_score}/100\n"
        content += f"    Business: {intel.business.business_legitimacy_score}/100\n"
        
        # Technology Stack
        content += self._format_subheader("TECHNOLOGY STACK")
        if intel.cms_detected:
            cms_info = intel.cms_detected
            if intel.cms_version:
                cms_info += f" v{intel.cms_version}"
            if intel.is_outdated_cms:
                cms_info += " (OUTDATED - Security Risk!)"
            content += f"  CMS: {cms_info}\n"
        else:
            content += "  CMS: Not detected\n"
        
        if intel.technologies:
            content += f"  Technologies: {', '.join(intel.technologies)}\n"
        
        content += f"  Mobile Friendly: {'Yes' if intel.is_mobile_friendly else 'No'}\n"
        content += f"  SSL/HTTPS: {'Yes' if intel.security.has_ssl else 'No'}\n"
        
        # Performance Section
        content += self._format_header("PERFORMANCE ANALYSIS")
        content += intel.performance.get_summary()
        
        # SEO Section
        content += self._format_header("SEO ANALYSIS")
        content += intel.seo.get_summary()
        
        # Security Section
        content += self._format_header("SECURITY ANALYSIS")
        content += intel.security.get_summary()
        
        # Accessibility Section
        content += self._format_header("ACCESSIBILITY ANALYSIS")
        content += intel.accessibility.get_summary()
        
        # Business Signals Section
        content += self._format_header("BUSINESS SIGNALS")
        content += intel.business.get_summary()
        
        # All Issues Summary
        content += self._format_header("ISSUES SUMMARY")
        all_issues = intel.get_all_issues()
        total_issues = sum(len(issues) for issues in all_issues.values())
        content += f"Total Issues Found: {total_issues}\n\n"
        
        for category, issues in all_issues.items():
            if issues:
                content += f"  {category.upper()} ({len(issues)} issues):\n"
                for issue in issues:
                    content += f"    • {issue}\n"
                content += "\n"
        
        # All Recommendations
        content += self._format_header("RECOMMENDATIONS")
        all_recommendations = self._get_all_prioritized_recommendations(intel)
        
        if all_recommendations:
            for priority in ['Critical', 'High', 'Medium', 'Low']:
                priority_recs = [r for r in all_recommendations if r['priority'] == priority]
                if priority_recs:
                    content += f"\n  {priority} Priority:\n"
                    for rec in priority_recs:
                        content += f"    • [{rec['category']}] {rec['recommendation']}\n"
        else:
            content += "  No major recommendations. Website is well-optimized.\n"
        
        # Action Plan
        content += self._format_header("SUGGESTED ACTION PLAN")
        content += self._get_action_plan(intel)
        
        return content
    
    def _get_executive_summary(self, intel: 'WebsiteIntelligence') -> str:
        """Generate executive summary text."""
        summary = f"\n  Website: {intel.domain}\n"
        summary += f"  Status: {'Online' if intel.status_code == 200 else f'Issues Detected (Status: {intel.status_code})'}\n"
        summary += f"  Overall Score: {intel.overall_score}/100\n\n"
        
        # Strengths
        strengths = self._get_strengths(intel)
        if strengths:
            summary += "  Key Strengths:\n"
            for strength in strengths[:5]:
                summary += f"    ✓ {strength}\n"
        
        # Critical Issues
        critical_issues = self._get_critical_issues(intel)
        if critical_issues:
            summary += "\n  Critical Issues:\n"
            for issue in critical_issues[:5]:
                summary += f"    ✗ {issue}\n"
        
        # Opportunities
        opportunities = self._get_opportunities(intel)
        if opportunities:
            summary += "\n  Opportunities:\n"
            for opp in opportunities[:3]:
                summary += f"    → {opp}\n"
        
        return summary
    
    def _get_strengths(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Identify website strengths."""
        strengths = []
        
        if intel.security.has_ssl:
            strengths.append("SSL/HTTPS enabled - secure connection")
        
        if intel.performance.load_time_metrics.median > 0 and intel.performance.load_time_metrics.median < 2:
            strengths.append(f"Fast load time ({intel.performance.load_time_metrics.median:.2f}s)")
        
        if intel.seo.seo_score >= 70:
            strengths.append(f"Good SEO score ({intel.seo.seo_score}/100)")
        
        if intel.seo.has_structured_data:
            strengths.append("Structured data implemented")
        
        if intel.business.business_legitimacy_score >= 70:
            strengths.append("Strong business legitimacy signals")
        
        if intel.accessibility.accessibility_score >= 60:
            strengths.append("Good accessibility practices")
        
        if intel.is_mobile_friendly:
            strengths.append("Mobile-friendly design")
        
        if intel.seo.has_sitemap:
            strengths.append("Sitemap present for search engines")
        
        if intel.business.has_privacy_policy:
            strengths.append("Privacy policy present")
        
        if len(intel.business.social_platforms) >= 3:
            strengths.append("Active social media presence")
        
        if intel.security.has_hsts:
            strengths.append("HSTS enabled for secure connections")
        
        if intel.seo.has_meta_description:
            strengths.append("Meta descriptions present")
        
        if intel.seo.h1_count == 1:
            strengths.append("Proper heading structure (single H1)")
        
        return strengths
    
    def _get_critical_issues(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Identify critical issues."""
        issues = []
        
        if not intel.security.has_ssl:
            issues.append("No SSL/HTTPS - major security and SEO issue")
        
        if intel.is_outdated_cms:
            issues.append(f"Outdated CMS ({intel.cms_detected}) - security vulnerability")
        
        if intel.performance.load_time_metrics.median > 5:
            issues.append(f"Very slow load time ({intel.performance.load_time_metrics.median:.2f}s)")
        
        if intel.seo.seo_score < 30:
            issues.append(f"Poor SEO score ({intel.seo.seo_score}/100)")
        
        if intel.security.security_headers_score < 30:
            issues.append("Missing critical security headers")
        
        if not intel.seo.has_meta_description:
            issues.append("Missing meta description")
        
        if intel.seo.h1_count == 0:
            issues.append("No H1 heading found")
        
        if intel.status_code != 200:
            issues.append(f"Website returned status code {intel.status_code}")
        
        if intel.error:
            issues.append(f"Error during analysis: {intel.error}")
        
        return issues
    
    def _get_opportunities(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Identify improvement opportunities."""
        opportunities = []
        
        if not intel.seo.has_structured_data:
            opportunities.append("Add structured data for rich search results")
        
        if not intel.seo.has_og_tags:
            opportunities.append("Add Open Graph tags for better social sharing")
        
        if intel.security.security_headers_score < 70:
            opportunities.append("Implement additional security headers")
        
        if intel.performance.load_time_metrics.median > 2:
            opportunities.append("Optimize load time for better user experience")
        
        if not intel.business.has_blog:
            opportunities.append("Add a blog for content marketing")
        
        if intel.seo.images_without_alt > 0:
            opportunities.append(f"Add alt text to {intel.seo.images_without_alt} images")
        
        if not intel.accessibility.has_aria_landmarks:
            opportunities.append("Improve accessibility with ARIA landmarks")
        
        if not intel.business.has_testimonials:
            opportunities.append("Add customer testimonials for social proof")
        
        return opportunities
    
    def _get_all_prioritized_recommendations(self, intel: 'WebsiteIntelligence') -> List[Dict]:
        """Get all recommendations from all areas, prioritized."""
        all_recs = []
        
        # Security recommendations (usually high priority)
        security_recs = self.security_report.get_recommendations(intel)
        for rec in security_recs:
            all_recs.append({
                'category': 'Security',
                'priority': rec['priority'],
                'recommendation': rec['title'] + ': ' + rec['action']
            })
        
        # Performance recommendations
        perf_recs = self.performance_report.get_recommendations(intel)
        for rec in perf_recs:
            priority = 'High' if 'Critical' in rec else 'Medium'
            all_recs.append({
                'category': 'Performance',
                'priority': priority,
                'recommendation': rec
            })
        
        # SEO recommendations
        seo_recs = intel.seo.get_recommendations()
        for rec in seo_recs:
            priority = 'High' if 'meta description' in rec.lower() else 'Medium'
            all_recs.append({
                'category': 'SEO',
                'priority': priority,
                'recommendation': rec
            })
        
        # Accessibility recommendations
        access_recs = intel.accessibility.get_recommendations()
        for rec in access_recs:
            all_recs.append({
                'category': 'Accessibility',
                'priority': 'Medium',
                'recommendation': rec
            })
        
        # Sort by priority
        priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        all_recs.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return all_recs
    
    def _get_action_plan(self, intel: 'WebsiteIntelligence') -> str:
        """Generate a suggested action plan."""
        plan = "\n"
        
        # Immediate actions (Critical/High priority)
        immediate = []
        if not intel.security.has_ssl:
            immediate.append("Enable HTTPS with SSL certificate")
        if intel.is_outdated_cms:
            immediate.append(f"Update {intel.cms_detected} to latest version")
        if intel.performance.load_time_metrics.median > 4:
            immediate.append("Address critical performance issues")
        if intel.error:
            immediate.append("Fix website errors preventing full analysis")
        
        if immediate:
            plan += "  IMMEDIATE (This Week):\n"
            for i, action in enumerate(immediate, 1):
                plan += f"    {i}. {action}\n"
            plan += "\n"
        
        # Short-term actions
        short_term = []
        if not intel.seo.has_meta_description:
            short_term.append("Add meta descriptions to all pages")
        if intel.seo.images_without_alt > 0:
            short_term.append("Add alt text to images")
        if not intel.security.has_hsts:
            short_term.append("Implement HSTS header")
        if not intel.seo.has_sitemap:
            short_term.append("Create and submit sitemap")
        if intel.seo.h1_count != 1:
            short_term.append("Fix heading structure (ensure single H1)")
        
        if short_term:
            plan += "  SHORT-TERM (This Month):\n"
            for i, action in enumerate(short_term, 1):
                plan += f"    {i}. {action}\n"
            plan += "\n"
        
        # Long-term actions
        long_term = []
        if not intel.seo.has_structured_data:
            long_term.append("Implement structured data")
        if intel.performance.load_time_metrics.median > 2:
            long_term.append("Comprehensive performance optimization")
        if not intel.accessibility.has_aria_landmarks:
            long_term.append("Improve accessibility with ARIA landmarks")
        if not intel.business.has_blog:
            long_term.append("Consider adding a blog for content marketing")
        if not intel.security.has_csp:
            long_term.append("Implement Content Security Policy")
        
        if long_term:
            plan += "  LONG-TERM (Next Quarter):\n"
            for i, action in enumerate(long_term, 1):
                plan += f"    {i}. {action}\n"
        
        if not immediate and not short_term and not long_term:
            plan += "  Website is well-optimized. Focus on:\n"
            plan += "    1. Regular security updates\n"
            plan += "    2. Content freshness\n"
            plan += "    3. Performance monitoring\n"
            plan += "    4. User experience improvements\n"
        
        return plan
    
    def _generate_pdf(self, intel: 'WebsiteIntelligence', output_path: Path) -> None:
        """Generate comprehensive PDF report."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.6*inch,
            bottomMargin=0.6*inch
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#1a1a2e')
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceBefore=25,
            spaceAfter=10,
            textColor=HexColor('#1a1a2e')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            spaceBefore=15,
            spaceAfter=8,
            textColor=HexColor('#16213e')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=5,
            textColor=HexColor('#0f3460')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=4
        )
        
        bullet_style = ParagraphStyle(
            'BulletStyle',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=20,
            spaceAfter=3
        )
        
        story = []
        
        # ===== TITLE PAGE =====
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("Comprehensive Website", title_style))
        story.append(Paragraph("Analysis Report", title_style))
        story.append(Spacer(1, 0.5*inch))
        story.append(HRFlowable(width="60%", thickness=2, color=HexColor('#e94560')))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<b>{intel.domain}</b>",
            ParagraphStyle('Domain', parent=styles['Heading2'], 
                          alignment=TA_CENTER, fontSize=18, textColor=HexColor('#333333'))
        ))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 0.8*inch))
        
        # Quick stats box
        quick_stats = [
            ['Overall Score', 'Performance', 'SEO', 'Security', 'Business'],
            [
                f"{intel.overall_score}/100",
                intel.performance.performance_grade,
                f"{intel.seo.seo_score}/100",
                f"{intel.security.security_headers_score}/100",
                f"{intel.business.business_legitimacy_score}/100"
            ]
        ]
        
        stats_table = Table(quick_stats, colWidths=[1.3*inch]*5)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('BACKGROUND', (0, 1), (-1, 1), HexColor('#f8f9fa')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(stats_table)
        
        story.append(PageBreak())
        
        # ===== EXECUTIVE SUMMARY =====
        story.append(Paragraph("Executive Summary", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        # Basic info table
        info_data = [
            ['Website', intel.domain],
            ['Final URL', intel.final_url or 'N/A'],
            ['Status', 'Online' if intel.status_code == 200 else f'Status {intel.status_code}'],
            ['Overall Score', f'{intel.overall_score}/100'],
            ['Lead Quality', intel.business.get_lead_quality()],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))
        
        # Strengths
        strengths = self._get_strengths(intel)
        if strengths:
            story.append(Paragraph("Key Strengths", heading_style))
            for strength in strengths[:6]:
                story.append(Paragraph(f"✓ {strength}", bullet_style))
            story.append(Spacer(1, 10))
        
        # Critical Issues
        critical_issues = self._get_critical_issues(intel)
        if critical_issues:
            story.append(Paragraph("Critical Issues", heading_style))
            for issue in critical_issues[:5]:
                story.append(Paragraph(f"✗ {issue}", bullet_style))
            story.append(Spacer(1, 10))
        
        # Opportunities
        opportunities = self._get_opportunities(intel)
        if opportunities:
            story.append(Paragraph("Opportunities", heading_style))
            for opp in opportunities[:4]:
                story.append(Paragraph(f"→ {opp}", bullet_style))
        
        story.append(PageBreak())
        
        # ===== TECHNOLOGY STACK =====
        story.append(Paragraph("Technology Stack", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        tech_data = [['Component', 'Details']]
        
        if intel.cms_detected:
            cms_text = intel.cms_detected
            if intel.cms_version:
                cms_text += f" v{intel.cms_version}"
            if intel.is_outdated_cms:
                cms_text += " (OUTDATED)"
            tech_data.append(['CMS', cms_text])
        else:
            tech_data.append(['CMS', 'Not detected'])
        
        tech_data.append(['Technologies', ', '.join(intel.technologies[:8]) if intel.technologies else 'None detected'])
        tech_data.append(['Mobile Friendly', '✓ Yes' if intel.is_mobile_friendly else '✗ No'])
        tech_data.append(['SSL/HTTPS', '✓ Enabled' if intel.security.has_ssl else '✗ Not Enabled'])
        
        tech_table = Table(tech_data, colWidths=[1.5*inch, 5*inch])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(tech_table)
        story.append(Spacer(1, 20))
        
        # ===== COMPONENT SCORES =====
        story.append(Paragraph("Component Scores", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        scores_data = [
            ['Component', 'Score', 'Grade', 'Status'],
            ['Performance', f'{intel.performance.get_numeric_score()}', intel.performance.performance_grade, self._get_score_status(intel.performance.get_numeric_score())],
            ['SEO', f'{intel.seo.seo_score}', self._get_grade_letter(intel.seo.seo_score), self._get_score_status(intel.seo.seo_score)],
            ['Security', f'{intel.security.security_headers_score}', intel.security.get_grade(), self._get_score_status(intel.security.security_headers_score)],
            ['Accessibility', f'{intel.accessibility.accessibility_score}', intel.accessibility.get_grade(), self._get_score_status(intel.accessibility.accessibility_score)],
            ['Business', f'{intel.business.business_legitimacy_score}', self._get_grade_letter(intel.business.business_legitimacy_score), self._get_score_status(intel.business.business_legitimacy_score)],
        ]
        
        scores_table = Table(scores_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
        ]))
        story.append(scores_table)
        
        story.append(PageBreak())
        
        # ===== PERFORMANCE DETAILS =====
        story.append(Paragraph("Performance Analysis", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        load_time = intel.performance.load_time_metrics
        if load_time.samples:
            perf_data = [
                ['Metric', 'Value'],
                ['Median Load Time', f'{load_time.median:.3f}s'],
                ['90th Percentile', f'{load_time.percentile_90:.3f}s'],
                ['95th Percentile', f'{load_time.percentile_95:.3f}s'],
                ['Standard Deviation', f'{load_time.std_dev:.3f}s'],
                ['Measurement Confidence', f'{load_time.confidence_score:.0%}'],
                ['HTML Size', f'{intel.performance.html_size_bytes/1024:.1f} KB'],
            ]
            
            perf_table = Table(perf_data, colWidths=[2.5*inch, 2*inch])
            perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(perf_table)
        else:
            story.append(Paragraph("No performance data available.", normal_style))
        
        story.append(Spacer(1, 20))
        
        # ===== SEO DETAILS =====
        story.append(Paragraph("SEO Analysis", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        seo = intel.seo
        seo_data = [
            ['Check', 'Status'],
            ['Meta Description', '✓' if seo.has_meta_description else '✗'],
            ['Open Graph Tags', '✓' if seo.has_og_tags else '✗'],
            ['Structured Data', '✓' if seo.has_structured_data else '✗'],
            ['Sitemap', '✓' if seo.has_sitemap else '✗'],
            ['Robots.txt', '✓' if seo.has_robots_txt else '✗'],
            ['H1 Count', f'{seo.h1_count} {"✓" if seo.h1_count == 1 else "⚠"}'],
            ['Images without Alt', f'{seo.images_without_alt} {"✓" if seo.images_without_alt == 0 else "⚠"}'],
        ]
        
        seo_table = Table(seo_data, colWidths=[2.5*inch, 1.5*inch])
        seo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(seo_table)
        
        story.append(Spacer(1, 20))
        
        # ===== SECURITY DETAILS =====
        story.append(Paragraph("Security Analysis", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        security = intel.security
        sec_data = [
            ['Security Header', 'Status'],
            ['SSL/HTTPS', '✓' if security.has_ssl else '✗ CRITICAL'],
            ['HSTS', '✓' if security.has_hsts else '✗'],
            ['Content Security Policy', '✓' if security.has_csp else '✗'],
            ['X-Frame-Options', '✓' if security.has_x_frame_options else '✗'],
            ['X-Content-Type-Options', '✓' if security.has_x_content_type_options else '✗'],
            ['X-XSS-Protection', '✓' if security.has_x_xss_protection else '✗'],
        ]
        
        sec_table = Table(sec_data, colWidths=[2.5*inch, 1.5*inch])
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(sec_table)
        
        story.append(PageBreak())
        
        # ===== BUSINESS SIGNALS =====
        story.append(Paragraph("Business Signals", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        business = intel.business
        bus_data = [
            ['Signal', 'Status'],
            ['Contact Page', '✓' if business.has_contact_page else '✗'],
            ['Contact Form', '✓' if business.has_contact_form else '✗'],
            ['Phone Number', '✓' if business.has_phone_number else '✗'],
            ['Email Address', '✓' if business.has_email else '✗'],
            ['Physical Address', '✓' if business.has_physical_address else '✗'],
            ['About Page', '✓' if business.has_about_page else '✗'],
            ['Privacy Policy', '✓' if business.has_privacy_policy else '✗'],
            ['Social Media', f'✓ {len(business.social_platforms)} platforms' if business.has_social_links else '✗'],
        ]
        
        bus_table = Table(bus_data, colWidths=[2.5*inch, 2*inch])
        bus_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(bus_table)
        
        story.append(Spacer(1, 20))
        
        # ===== ACTION PLAN =====
        story.append(Paragraph("Suggested Action Plan", section_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e94560')))
        story.append(Spacer(1, 10))
        
        action_plan = self._get_action_plan(intel)
        for line in action_plan.strip().split('\n'):
            if line.strip():
                if 'IMMEDIATE' in line or 'SHORT-TERM' in line or 'LONG-TERM' in line:
                    story.append(Paragraph(f"<b>{line.strip()}</b>", subheading_style))
                else:
                    story.append(Paragraph(line.strip(), normal_style))
        
        # Build PDF
        doc.build(story)
    
    def _get_score_status(self, score: int) -> str:
        """Get status text for a score."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Needs Work"
        else:
            return "Poor"
    
    def get_summary_dict(self, intel: 'WebsiteIntelligence') -> Dict:
        """Get a complete summary dictionary."""
        return {
            'domain': intel.domain,
            'overall_score': intel.overall_score,
            'buyer_priority_score': intel.buyer_priority_score,
            'lead_quality': intel.business.get_lead_quality(),
            'performance_grade': intel.performance.performance_grade,
            'seo_score': intel.seo.seo_score,
            'security_score': intel.security.security_headers_score,
            'accessibility_score': intel.accessibility.accessibility_score,
            'business_score': intel.business.business_legitimacy_score,
            'strengths_count': len(self._get_strengths(intel)),
            'issues_count': len(self._get_critical_issues(intel)),
            'opportunities_count': len(self._get_opportunities(intel)),
            'cms': intel.cms_detected,
            'is_outdated': intel.is_outdated_cms,
            'has_ssl': intel.security.has_ssl,
        }