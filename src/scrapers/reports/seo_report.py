"""SEO-focused report generator."""

from pathlib import Path
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from .base_report import BaseReport

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class SEOReport(BaseReport):
    """Generates SEO-focused reports for website intelligence."""
    
    REPORT_TYPE = "seo"
    
    def generate(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate SEO report as PDF.
        
        Args:
            intel: WebsiteIntelligence object
            filename: Output filename
            
        Returns:
            Path to the generated report
        """
        if not self._reportlab_available:
            # Fallback to text report
            return self.save_text_report(intel, filename)
        
        if filename is None:
            filename = self._generate_filename(intel, 'pdf')
        
        output_path = self.output_dir / filename
        self._generate_pdf(intel, output_path)
        
        return output_path
    
    def get_text_content(self, intel: 'WebsiteIntelligence') -> str:
        """Get SEO report as plain text."""
        seo = intel.seo
        
        content = self._format_header(f"SEO ANALYSIS REPORT: {intel.domain}")
        content += f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"URL: {intel.final_url or intel.domain}\n"
        
        # Overall Score
        content += self._format_subheader("OVERALL SEO SCORE")
        content += f"Score: {seo.seo_score}/100 (Grade: {self._get_grade_letter(seo.seo_score)})\n"
        
        # Meta Tags Section
        content += self._format_subheader("META TAGS")
        content += f"  Meta Description: {self._get_status_symbol(seo.has_meta_description)}\n"
        content += f"  Meta Keywords: {self._get_status_symbol(seo.has_meta_keywords)}\n"
        content += f"  Canonical URL: {self._get_status_symbol(bool(seo.canonical_url))}\n"
        if seo.canonical_url:
            content += f"    └─ {seo.canonical_url}\n"
        
        # Social Meta Tags
        content += self._format_subheader("SOCIAL MEDIA TAGS")
        content += f"  Open Graph Tags: {self._get_status_symbol(seo.has_og_tags)}\n"
        content += f"  Twitter Cards: {self._get_status_symbol(seo.has_twitter_cards)}\n"
        
        # Structured Data
        content += self._format_subheader("STRUCTURED DATA")
        content += f"  JSON-LD / Microdata: {self._get_status_symbol(seo.has_structured_data)}\n"
        
        # Crawlability
        content += self._format_subheader("CRAWLABILITY")
        content += f"  Sitemap.xml: {self._get_status_symbol(seo.has_sitemap)}\n"
        content += f"  Robots.txt: {self._get_status_symbol(seo.has_robots_txt)}\n"
        
        # Content Structure
        content += self._format_subheader("CONTENT STRUCTURE")
        h1_status = "✓" if seo.h1_count == 1 else ("⚠ Multiple" if seo.h1_count > 1 else "✗ Missing")
        content += f"  H1 Tags: {seo.h1_count} {h1_status}\n"
        content += f"  H2 Tags: {seo.h2_count}\n"
        
        # Images
        content += self._format_subheader("IMAGES")
        content += f"  Total Images: {seo.image_count}\n"
        content += f"  Missing Alt Text: {seo.images_without_alt}\n"
        if seo.image_count > 0:
            alt_percentage = ((seo.image_count - seo.images_without_alt) / seo.image_count) * 100
            content += f"  Alt Text Coverage: {alt_percentage:.1f}%\n"
        
        # Links
        content += self._format_subheader("LINKS")
        content += f"  Internal Links: {seo.internal_links}\n"
        content += f"  External Links: {seo.external_links}\n"
        
        # Issues
        issues = seo.get_issues()
        if issues:
            content += self._format_subheader("ISSUES FOUND")
            for i, issue in enumerate(issues, 1):
                content += f"  {i}. {issue}\n"
        
        # Recommendations
        recommendations = seo.get_recommendations()
        if recommendations:
            content += self._format_subheader("RECOMMENDATIONS")
            for i, rec in enumerate(recommendations, 1):
                content += f"  {i}. {rec}\n"
        
        return content
    
    def _generate_pdf(self, intel: 'WebsiteIntelligence', output_path: Path) -> None:
        """Generate PDF version of SEO report."""
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
        
        seo = intel.seo
        story = []
        
        # Title
        story.append(Paragraph("SEO Analysis Report", title_style))
        story.append(Paragraph(
            f"<b>{intel.domain}</b>",
            ParagraphStyle('Domain', parent=styles['Heading3'], 
                          alignment=TA_CENTER, textColor=HexColor('#e94560'))
        ))
        story.append(Spacer(1, 20))
        
        # Overall Score
        story.append(Paragraph("Overall SEO Score", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        score_color = HexColor('#27ae60') if seo.seo_score >= 70 else (
            HexColor('#f39c12') if seo.seo_score >= 50 else HexColor('#e74c3c')
        )
        
        story.append(Paragraph(
            f"<font size='24' color='{score_color.hexval()}'><b>{seo.seo_score}/100</b></font> "
            f"(Grade: {self._get_grade_letter(seo.seo_score)})",
            ParagraphStyle('Score', parent=styles['Normal'], alignment=TA_CENTER, spaceBefore=10)
        ))
        story.append(Spacer(1, 20))
        
        # Checklist Table
        story.append(Paragraph("SEO Checklist", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        checklist_data = [
            ['Item', 'Status', 'Impact'],
            ['Meta Description', self._get_status_symbol(seo.has_meta_description), 'High'],
            ['Open Graph Tags', self._get_status_symbol(seo.has_og_tags), 'Medium'],
            ['Twitter Cards', self._get_status_symbol(seo.has_twitter_cards), 'Low'],
            ['Structured Data', self._get_status_symbol(seo.has_structured_data), 'High'],
            ['Sitemap.xml', self._get_status_symbol(seo.has_sitemap), 'High'],
            ['Robots.txt', self._get_status_symbol(seo.has_robots_txt), 'Medium'],
            ['Single H1 Tag', self._get_status_symbol(seo.h1_count == 1), 'Medium'],
            ['Images with Alt', self._get_status_symbol(seo.images_without_alt == 0), 'Medium'],
            ['Canonical URL', self._get_status_symbol(bool(seo.canonical_url)), 'Medium'],
        ]
        
        checklist_table = Table(checklist_data, colWidths=[3*inch, 1*inch, 1*inch])
        checklist_table.setStyle(TableStyle([
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
        story.append(checklist_table)
        story.append(Spacer(1, 20))
        
        # Content Statistics
        story.append(Paragraph("Content Statistics", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        stats_data = [
            ['Metric', 'Count'],
            ['H1 Tags', str(seo.h1_count)],
            ['H2 Tags', str(seo.h2_count)],
            ['Total Images', str(seo.image_count)],
            ['Images Missing Alt', str(seo.images_without_alt)],
            ['Internal Links', str(seo.internal_links)],
            ['External Links', str(seo.external_links)],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Issues
        issues = seo.get_issues()
        if issues:
            story.append(Paragraph("Issues Found", heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
            for issue in issues:
                story.append(Paragraph(f"• {issue}", normal_style))
            story.append(Spacer(1, 15))
        
        # Recommendations
        recommendations = seo.get_recommendations()
        if recommendations:
            story.append(Paragraph("Recommendations", heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", normal_style))
        
        doc.build(story)
    
    def get_issues_summary(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Get a summary of SEO issues."""
        return intel.seo.get_issues()
    
    def get_recommendations(self, intel: 'WebsiteIntelligence') -> List[str]:
        """Get SEO recommendations."""
        return intel.seo.get_recommendations()