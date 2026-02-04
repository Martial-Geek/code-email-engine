"""PDF exporter for website intelligence reports."""

from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class PDFExporter:
    """
    Exports website intelligence data to PDF format.
    
    Requires reportlab library: pip install reportlab
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize PDF exporter.
        
        Args:
            output_dir: Directory to save PDF files
        """
        self.output_dir = output_dir or Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if reportlab is available
        self._reportlab_available = self._check_reportlab()
    
    def _check_reportlab(self) -> bool:
        """Check if reportlab library is available."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate
            return True
        except ImportError:
            return False
    
    def export_single(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Export a single website analysis to PDF.
        
        Args:
            intel: WebsiteIntelligence object
            filename: Output filename
            
        Returns:
            Path to the saved PDF file
        """
        if not self._reportlab_available:
            raise ImportError(
                "reportlab is required for PDF export. "
                "Install it with: pip install reportlab"
            )
        
        if filename is None:
            safe_domain = intel.domain.replace('.', '_').replace('/', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{safe_domain}_{timestamp}.pdf"
        
        output_path = self.output_dir / filename
        
        self._generate_single_report(intel, output_path)
        
        return output_path
    
    def export_batch(
        self,
        results: List['WebsiteIntelligence'],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export multiple website analyses to a single PDF.
        
        Args:
            results: List of WebsiteIntelligence objects
            filename: Output filename
            
        Returns:
            Path to the saved PDF file
        """
        if not self._reportlab_available:
            raise ImportError(
                "reportlab is required for PDF export. "
                "Install it with: pip install reportlab"
            )
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_report_{timestamp}.pdf"
        
        output_path = self.output_dir / filename
        
        self._generate_batch_report(results, output_path)
        
        return output_path
    
    def _generate_single_report(
        self, 
        intel: 'WebsiteIntelligence', 
        output_path: Path
    ) -> None:
        """Generate PDF report for a single website."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor, black, green, red, orange
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#1a1a2e')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=HexColor('#16213e')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=HexColor('#0f3460')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Build document content
        story = []
        
        # Title
        story.append(Paragraph(f"Website Analysis Report", title_style))
        story.append(Paragraph(f"<b>{intel.domain}</b>", 
                              ParagraphStyle('Domain', parent=styles['Heading2'], 
                                           alignment=TA_CENTER, textColor=HexColor('#e94560'))))
        story.append(Spacer(1, 20))
        
        # Analysis metadata
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cccccc')))
        story.append(Spacer(1, 10))
        
        meta_data = [
            ['Analysis Date:', intel.analysis_timestamp],
            ['Final URL:', intel.final_url or 'N/A'],
            ['Status:', '✓ Online' if intel.status_code == 200 else f'⚠ Status {intel.status_code}'],
        ]
        
        meta_table = Table(meta_data, colWidths=[1.5*inch, 5*inch])
        meta_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # Overall Scores Section
        story.append(Paragraph("Overall Scores", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        scores_data = [
            ['Metric', 'Score', 'Grade'],
            ['Overall Website Score', f'{intel.overall_score}/100', self._get_grade_letter(intel.overall_score)],
            ['Buyer Priority Score', str(intel.buyer_priority_score), '-'],
            ['Performance', f'{intel.performance.get_numeric_score()}/100', intel.performance.performance_grade],
            ['SEO', f'{intel.seo.seo_score}/100', self._get_grade_letter(intel.seo.seo_score)],
            ['Security', f'{intel.security.security_headers_score}/100', intel.security.get_grade()],
            ['Accessibility', f'{intel.accessibility.accessibility_score}/100', intel.accessibility.get_grade()],
            ['Business Legitimacy', f'{intel.business.business_legitimacy_score}/100', self._get_grade_letter(intel.business.business_legitimacy_score)],
        ]
        
        scores_table = Table(scores_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
        ]))
        story.append(scores_table)
        story.append(Spacer(1, 25))
        
        # Technology Section
        story.append(Paragraph("Technology Stack", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        tech_info = []
        if intel.cms_detected:
            cms_text = intel.cms_detected
            if intel.cms_version:
                cms_text += f" v{intel.cms_version}"
            if intel.is_outdated_cms:
                cms_text += " (OUTDATED)"
            tech_info.append(['CMS:', cms_text])
        else:
            tech_info.append(['CMS:', 'Not detected'])
        
        if intel.technologies:
            tech_info.append(['Technologies:', ', '.join(intel.technologies[:10])])
        
        tech_info.append(['Mobile Friendly:', '✓ Yes' if intel.is_mobile_friendly else '✗ No'])
        tech_info.append(['SSL/HTTPS:', '✓ Yes' if intel.security.has_ssl else '✗ No'])
        
        tech_table = Table(tech_info, colWidths=[1.5*inch, 5*inch])
        tech_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tech_table)
        story.append(Spacer(1, 25))
        
        # Performance Section
        story.append(Paragraph("Performance Analysis", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        load_metrics = intel.performance.load_time_metrics
        perf_data = [
            ['Load Time (Median):', f'{load_metrics.median:.3f}s' if load_metrics.median else 'N/A'],
            ['Load Time (90th Percentile):', f'{load_metrics.percentile_90:.3f}s' if load_metrics.percentile_90 else 'N/A'],
            ['HTML Size:', f'{intel.performance.html_size_bytes / 1024:.1f} KB'],
            ['Measurement Confidence:', f'{load_metrics.confidence_score:.0%}' if load_metrics.confidence_score else 'N/A'],
        ]
        
        perf_table = Table(perf_data, colWidths=[2.5*inch, 4*inch])
        perf_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(perf_table)
        story.append(Spacer(1, 25))
        
        # SEO Section
        story.append(Paragraph("SEO Analysis", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        seo = intel.seo
        seo_checklist = [
            ['Check', 'Status'],
            ['Meta Description', '✓' if seo.has_meta_description else '✗'],
            ['Open Graph Tags', '✓' if seo.has_og_tags else '✗'],
            ['Twitter Cards', '✓' if seo.has_twitter_cards else '✗'],
            ['Structured Data', '✓' if seo.has_structured_data else '✗'],
            ['Sitemap', '✓' if seo.has_sitemap else '✗'],
            ['Robots.txt', '✓' if seo.has_robots_txt else '✗'],
            ['H1 Count', str(seo.h1_count) + (' ✓' if seo.h1_count == 1 else ' ⚠')],
            ['Images without Alt', str(seo.images_without_alt) + (' ✓' if seo.images_without_alt == 0 else ' ⚠')],
        ]
        
        seo_table = Table(seo_checklist, colWidths=[3*inch, 2*inch])
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
        
        # SEO Issues
        seo_issues = seo.get_issues()
        if seo_issues:
            story.append(Spacer(1, 15))
            story.append(Paragraph("Issues Found:", subheading_style))
            for issue in seo_issues:
                story.append(Paragraph(f"• {issue}", normal_style))
        
        story.append(Spacer(1, 25))
        
        # Security Section
        story.append(Paragraph("Security Analysis", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        security = intel.security
        security_checklist = [
            ['Security Header', 'Status'],
            ['SSL/HTTPS', '✓' if security.has_ssl else '✗ CRITICAL'],
            ['HSTS', '✓' if security.has_hsts else '✗'],
            ['Content Security Policy', '✓' if security.has_csp else '✗'],
            ['X-Frame-Options', '✓' if security.has_x_frame_options else '✗'],
            ['X-Content-Type-Options', '✓' if security.has_x_content_type_options else '✗'],
            ['X-XSS-Protection', '✓' if security.has_x_xss_protection else '✗'],
        ]
        
        security_table = Table(security_checklist, colWidths=[3*inch, 2*inch])
        security_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(security_table)
        story.append(Spacer(1, 25))
        
        # Business Signals Section
        story.append(Paragraph("Business Signals", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        business = intel.business
        business_data = [
            ['Signal', 'Status'],
            ['Contact Page', '✓' if business.has_contact_page else '✗'],
            ['Contact Form', '✓' if business.has_contact_form else '✗'],
            ['Phone Number', '✓' if business.has_phone_number else '✗'],
            ['Email Address', '✓' if business.has_email else '✗'],
            ['Physical Address', '✓' if business.has_physical_address else '✗'],
            ['About Page', '✓' if business.has_about_page else '✗'],
            ['Privacy Policy', '✓' if business.has_privacy_policy else '✗'],
            ['Social Media Links', '✓' if business.has_social_links else '✗'],
        ]
        
        if business.social_platforms:
            business_data.append(['Social Platforms', ', '.join(business.social_platforms)])
        
        if business.copyright_year:
            business_data.append(['Copyright Year', str(business.copyright_year)])
        
        business_table = Table(business_data, colWidths=[3*inch, 2.5*inch])
        business_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(business_table)
        
        story.append(Spacer(1, 15))
        story.append(Paragraph(f"Lead Quality: <b>{business.get_lead_quality()}</b>", normal_style))
        
        # Build the PDF
        doc.build(story)
    
    def _generate_batch_report(
        self, 
        results: List['WebsiteIntelligence'], 
        output_path: Path
    ) -> None:
        """Generate PDF report for multiple websites."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#1a1a2e')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=HexColor('#16213e')
        )
        
        story = []
        
        # Title page
        story.append(Paragraph("Batch Website Analysis Report", title_style))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)
        ))
        story.append(Paragraph(
            f"Total Websites Analyzed: {len(results)}",
            ParagraphStyle('Count', parent=styles['Normal'], alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 30))
        
        # Summary statistics
        story.append(Paragraph("Summary Statistics", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        successful = [r for r in results if r.error is None]
        failed = len(results) - len(successful)
        
        if successful:
            avg_overall = sum(r.overall_score for r in successful) / len(successful)
            avg_seo = sum(r.seo.seo_score for r in successful) / len(successful)
            avg_security = sum(r.security.security_headers_score for r in successful) / len(successful)
            with_ssl = len([r for r in successful if r.security.has_ssl])
            high_priority = len([r for r in successful if r.buyer_priority_score >= 50])
        else:
            avg_overall = avg_seo = avg_security = with_ssl = high_priority = 0
        
        summary_data = [
            ['Metric', 'Value'],
            ['Successfully Analyzed', str(len(successful))],
            ['Failed', str(failed)],
            ['Average Overall Score', f'{avg_overall:.1f}'],
            ['Average SEO Score', f'{avg_seo:.1f}'],
            ['Average Security Score', f'{avg_security:.1f}'],
            ['Sites with SSL', f'{with_ssl} ({with_ssl/len(successful)*100:.1f}%)' if successful else '0'],
            ['High Priority Leads', str(high_priority)],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Top leads table
        story.append(Paragraph("Top Priority Leads", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        # Sort by buyer priority score
        top_leads = sorted(successful, key=lambda x: x.buyer_priority_score, reverse=True)[:20]
        
        leads_data = [['Domain', 'Priority', 'Overall', 'SEO', 'Security', 'CMS']]
        for lead in top_leads:
            leads_data.append([
                lead.domain[:30],
                str(lead.buyer_priority_score),
                str(lead.overall_score),
                str(lead.seo.seo_score),
                str(lead.security.security_headers_score),
                lead.cms_detected or '-'
            ])
        
        leads_table = Table(leads_data, colWidths=[2*inch, 0.7*inch, 0.7*inch, 0.6*inch, 0.7*inch, 1*inch])
        leads_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
        ]))
        story.append(leads_table)
        
        # Build the PDF
        doc.build(story)
    
    def _get_grade_letter(self, score: int) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def export_text_report(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Export a plain text report (fallback when reportlab not available).
        
        Args:
            intel: WebsiteIntelligence object
            filename: Output filename
            
        Returns:
            Path to the saved text file
        """
        if filename is None:
            safe_domain = intel.domain.replace('.', '_').replace('/', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{safe_domain}_{timestamp}.txt"
        
        output_path = self.output_dir / filename
        
        report_content = intel.get_full_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_path