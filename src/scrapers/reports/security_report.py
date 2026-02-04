"""Security-focused report generator."""

from pathlib import Path
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime

from .base_report import BaseReport

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class SecurityReport(BaseReport):
    """Generates security-focused reports for website intelligence."""
    
    REPORT_TYPE = "security"
    
    # Security header descriptions
    HEADER_DESCRIPTIONS = {
        'ssl': {
            'name': 'SSL/HTTPS',
            'description': 'Encrypts data in transit between the user and server.',
            'impact': 'Critical',
            'fix': 'Obtain and install an SSL certificate. Many hosts offer free certificates via Let\'s Encrypt.'
        },
        'hsts': {
            'name': 'HTTP Strict Transport Security (HSTS)',
            'description': 'Forces browsers to only use HTTPS connections.',
            'impact': 'High',
            'fix': 'Add header: Strict-Transport-Security: max-age=31536000; includeSubDomains'
        },
        'csp': {
            'name': 'Content Security Policy (CSP)',
            'description': 'Prevents XSS attacks by controlling resource loading.',
            'impact': 'High',
            'fix': 'Define a CSP header that specifies allowed content sources.'
        },
        'x_frame_options': {
            'name': 'X-Frame-Options',
            'description': 'Prevents clickjacking by controlling iframe embedding.',
            'impact': 'Medium',
            'fix': 'Add header: X-Frame-Options: DENY or SAMEORIGIN'
        },
        'x_content_type_options': {
            'name': 'X-Content-Type-Options',
            'description': 'Prevents MIME-type sniffing attacks.',
            'impact': 'Medium',
            'fix': 'Add header: X-Content-Type-Options: nosniff'
        },
        'x_xss_protection': {
            'name': 'X-XSS-Protection',
            'description': 'Enables browser\'s built-in XSS filter.',
            'impact': 'Low',
            'fix': 'Add header: X-XSS-Protection: 1; mode=block'
        }
    }
    
    def generate(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate security report as PDF.
        
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
        """Get security report as plain text."""
        security = intel.security
        
        content = self._format_header(f"SECURITY ANALYSIS REPORT: {intel.domain}")
        content += f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"URL: {intel.final_url or intel.domain}\n"
        
        # Overall Score
        content += self._format_subheader("OVERALL SECURITY SCORE")
        content += f"Score: {security.security_headers_score}/100\n"
        content += f"Grade: {security.get_grade()}\n"
        
        # Risk Level
        risk_level = self._get_risk_level(security.security_headers_score)
        content += f"Risk Level: {risk_level}\n"
        
        # Security Headers Status
        content += self._format_subheader("SECURITY HEADERS STATUS")
        
        headers_status = self._get_headers_status(intel)
        for header_key, status in headers_status.items():
            header_info = self.HEADER_DESCRIPTIONS[header_key]
            symbol = self._get_status_symbol(status['present'])
            impact_indicator = f"[{header_info['impact']}]"
            content += f"\n  {symbol} {header_info['name']} {impact_indicator}\n"
            content += f"      Status: {'Present' if status['present'] else 'Missing'}\n"
            content += f"      Description: {header_info['description']}\n"
        
        # Vulnerabilities
        content += self._format_subheader("POTENTIAL VULNERABILITIES")
        vulnerabilities = self._get_vulnerabilities(intel)
        if vulnerabilities:
            for i, vuln in enumerate(vulnerabilities, 1):
                content += f"\n  {i}. {vuln['name']}\n"
                content += f"     Severity: {vuln['severity']}\n"
                content += f"     Description: {vuln['description']}\n"
        else:
            content += "  No critical vulnerabilities detected.\n"
        
        # Issues Found
        content += self._format_subheader("ISSUES FOUND")
        issues = security.get_issues()
        if issues:
            for i, issue in enumerate(issues, 1):
                content += f"  {i}. {issue}\n"
        else:
            content += "  No issues found.\n"
        
        # Recommendations
        content += self._format_subheader("RECOMMENDATIONS")
        recommendations = self.get_recommendations(intel)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                content += f"\n  {i}. {rec['title']}\n"
                content += f"     Priority: {rec['priority']}\n"
                content += f"     Action: {rec['action']}\n"
        else:
            content += "  Security posture is good. Continue monitoring.\n"
        
        # Implementation Guide
        content += self._format_subheader("IMPLEMENTATION GUIDE")
        missing_headers = [k for k, v in headers_status.items() if not v['present']]
        if missing_headers:
            content += "\n  Recommended header configurations:\n\n"
            for header_key in missing_headers:
                header_info = self.HEADER_DESCRIPTIONS[header_key]
                content += f"  {header_info['name']}:\n"
                content += f"    {header_info['fix']}\n\n"
        else:
            content += "  All recommended security headers are in place.\n"
        
        return content
    
    def _get_risk_level(self, score: int) -> str:
        """Determine risk level based on security score."""
        if score >= 80:
            return "Low Risk"
        elif score >= 60:
            return "Moderate Risk"
        elif score >= 40:
            return "Elevated Risk"
        elif score >= 20:
            return "High Risk"
        else:
            return "Critical Risk"
    
    def _get_headers_status(self, intel: 'WebsiteIntelligence') -> Dict:
        """Get status of all security headers."""
        security = intel.security
        
        return {
            'ssl': {'present': security.has_ssl},
            'hsts': {'present': security.has_hsts},
            'csp': {'present': security.has_csp},
            'x_frame_options': {'present': security.has_x_frame_options},
            'x_content_type_options': {'present': security.has_x_content_type_options},
            'x_xss_protection': {'present': security.has_x_xss_protection},
        }
    
    def _get_vulnerabilities(self, intel: 'WebsiteIntelligence') -> List[Dict]:
        """Identify potential vulnerabilities based on missing security measures."""
        vulnerabilities = []
        security = intel.security
        
        if not security.has_ssl:
            vulnerabilities.append({
                'name': 'No HTTPS/SSL Encryption',
                'severity': 'Critical',
                'description': 'Data transmitted between users and the server is not encrypted, '
                              'making it vulnerable to interception (man-in-the-middle attacks).'
            })
        
        if not security.has_hsts and security.has_ssl:
            vulnerabilities.append({
                'name': 'SSL Stripping Vulnerability',
                'severity': 'High',
                'description': 'Without HSTS, attackers may be able to downgrade HTTPS '
                              'connections to HTTP through SSL stripping attacks.'
            })
        
        if not security.has_csp:
            vulnerabilities.append({
                'name': 'Cross-Site Scripting (XSS) Risk',
                'severity': 'High',
                'description': 'Without CSP, the site is more vulnerable to XSS attacks '
                              'where malicious scripts can be injected and executed.'
            })
        
        if not security.has_x_frame_options:
            vulnerabilities.append({
                'name': 'Clickjacking Vulnerability',
                'severity': 'Medium',
                'description': 'The site can be embedded in iframes, making it vulnerable '
                              'to clickjacking attacks where users are tricked into clicking hidden elements.'
            })
        
        if not security.has_x_content_type_options:
            vulnerabilities.append({
                'name': 'MIME Sniffing Risk',
                'severity': 'Medium',
                'description': 'Browsers may interpret files differently than intended, '
                              'potentially executing malicious content.'
            })
        
        # Check for outdated CMS
        if intel.is_outdated_cms:
            vulnerabilities.append({
                'name': f'Outdated CMS ({intel.cms_detected})',
                'severity': 'High',
                'description': f'Running an outdated version of {intel.cms_detected} may expose '
                              'known security vulnerabilities that have been patched in newer versions.'
            })
        
        return vulnerabilities
    
    def get_recommendations(self, intel: 'WebsiteIntelligence') -> List[Dict]:
        """Get prioritized security recommendations."""
        recommendations = []
        security = intel.security
        
        if not security.has_ssl:
            recommendations.append({
                'title': 'Enable HTTPS with SSL Certificate',
                'priority': 'Critical',
                'action': 'Obtain an SSL certificate (free via Let\'s Encrypt) and configure '
                         'your server to use HTTPS. Redirect all HTTP traffic to HTTPS.'
            })
        
        if not security.has_hsts:
            recommendations.append({
                'title': 'Implement HSTS Header',
                'priority': 'High',
                'action': 'Add Strict-Transport-Security header with appropriate max-age. '
                         'Start with a short duration and increase after testing.'
            })
        
        if not security.has_csp:
            recommendations.append({
                'title': 'Implement Content Security Policy',
                'priority': 'High',
                'action': 'Define a Content-Security-Policy header. Start with report-only mode '
                         'to identify issues before enforcing.'
            })
        
        if not security.has_x_frame_options:
            recommendations.append({
                'title': 'Add X-Frame-Options Header',
                'priority': 'Medium',
                'action': 'Add X-Frame-Options: DENY (or SAMEORIGIN if iframes are needed) '
                         'to prevent clickjacking attacks.'
            })
        
        if not security.has_x_content_type_options:
            recommendations.append({
                'title': 'Add X-Content-Type-Options Header',
                'priority': 'Medium',
                'action': 'Add X-Content-Type-Options: nosniff to prevent MIME-type sniffing.'
            })
        
        if not security.has_x_xss_protection:
            recommendations.append({
                'title': 'Add X-XSS-Protection Header',
                'priority': 'Low',
                'action': 'Add X-XSS-Protection: 1; mode=block (though CSP is preferred).'
            })
        
        if intel.is_outdated_cms:
            recommendations.append({
                'title': f'Update {intel.cms_detected} CMS',
                'priority': 'High',
                'action': f'Update {intel.cms_detected} to the latest version. '
                         'Backup your site before updating and test in a staging environment.'
            })
        
        return recommendations
    
    def _generate_pdf(self, intel: 'WebsiteIntelligence', output_path: Path) -> None:
        """Generate PDF version of security report."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak
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
            fontSize=10,
            spaceAfter=6
        )
        
        security = intel.security
        story = []
        
        # Title
        story.append(Paragraph("Security Analysis Report", title_style))
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
        
        # Overall Score and Risk Level
        story.append(Paragraph("Security Overview", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        risk_level = self._get_risk_level(security.security_headers_score)
        risk_colors = {
            'Low Risk': '#27ae60',
            'Moderate Risk': '#f39c12',
            'Elevated Risk': '#e67e22',
            'High Risk': '#e74c3c',
            'Critical Risk': '#c0392b'
        }
        risk_color = HexColor(risk_colors.get(risk_level, '#95a5a6'))
        
        overview_data = [
            ['Metric', 'Value'],
            ['Security Score', f'{security.security_headers_score}/100'],
            ['Grade', security.get_grade()],
            ['Risk Level', risk_level],
            ['SSL/HTTPS', '✓ Enabled' if security.has_ssl else '✗ Not Enabled'],
        ]
        
        overview_table = Table(overview_data, colWidths=[2.5*inch, 3*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Security Headers Table
        story.append(Paragraph("Security Headers Analysis", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
        
        headers_status = self._get_headers_status(intel)
        headers_data = [['Security Header', 'Status', 'Impact']]
        
        for header_key, status in headers_status.items():
            header_info = self.HEADER_DESCRIPTIONS[header_key]
            status_text = '✓ Present' if status['present'] else '✗ Missing'
            headers_data.append([
                header_info['name'],
                status_text,
                header_info['impact']
            ])
        
        headers_table = Table(headers_data, colWidths=[3*inch, 1.2*inch, 1*inch])
        headers_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
        ]))
        story.append(headers_table)
        story.append(Spacer(1, 20))
        
        # Vulnerabilities
        vulnerabilities = self._get_vulnerabilities(intel)
        if vulnerabilities:
            story.append(Paragraph("Potential Vulnerabilities", heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
            
            for vuln in vulnerabilities:
                severity_colors = {
                    'Critical': '#c0392b',
                    'High': '#e74c3c',
                    'Medium': '#f39c12',
                    'Low': '#3498db'
                }
                sev_color = severity_colors.get(vuln['severity'], '#95a5a6')
                
                story.append(Paragraph(
                    f"<b>{vuln['name']}</b> "
                    f"<font color='{sev_color}'>[{vuln['severity']}]</font>",
                    subheading_style
                ))
                story.append(Paragraph(vuln['description'], normal_style))
                story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 15))
        
        # Recommendations
        recommendations = self.get_recommendations(intel)
        if recommendations:
            story.append(Paragraph("Recommendations", heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e94560')))
            
            for i, rec in enumerate(recommendations, 1):
                priority_colors = {
                    'Critical': '#c0392b',
                    'High': '#e74c3c',
                    'Medium': '#f39c12',
                    'Low': '#3498db'
                }
                pri_color = priority_colors.get(rec['priority'], '#95a5a6')
                
                story.append(Paragraph(
                    f"<b>{i}. {rec['title']}</b> "
                    f"<font color='{pri_color}'>[{rec['priority']}]</font>",
                    subheading_style
                ))
                story.append(Paragraph(rec['action'], normal_style))
                story.append(Spacer(1, 5))
        
        doc.build(story)
    
    def get_security_summary(self, intel: 'WebsiteIntelligence') -> Dict:
        """Get a summary dictionary of security status."""
        security = intel.security
        
        return {
            'score': security.security_headers_score,
            'grade': security.get_grade(),
            'risk_level': self._get_risk_level(security.security_headers_score),
            'has_ssl': security.has_ssl,
            'has_hsts': security.has_hsts,
            'has_csp': security.has_csp,
            'vulnerabilities_count': len(self._get_vulnerabilities(intel)),
            'recommendations_count': len(self.get_recommendations(intel)),
        }