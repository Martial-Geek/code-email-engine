"""Base report class for website intelligence reports."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class BaseReport(ABC):
    """
    Abstract base class for report generators.
    
    All specific report types (SEO, Performance, Security, etc.) 
    inherit from this class.
    """
    
    REPORT_TYPE = "base"
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir or Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for reportlab availability
        self._reportlab_available = self._check_reportlab()
    
    def _check_reportlab(self) -> bool:
        """Check if reportlab library is available."""
        try:
            from reportlab.lib.pagesizes import letter
            return True
        except ImportError:
            return False
    
    @abstractmethod
    def generate(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate the report.
        
        Args:
            intel: WebsiteIntelligence object
            filename: Output filename
            
        Returns:
            Path to the generated report
        """
        pass
    
    @abstractmethod
    def get_text_content(self, intel: 'WebsiteIntelligence') -> str:
        """
        Get the report content as plain text.
        
        Args:
            intel: WebsiteIntelligence object
            
        Returns:
            Report content as string
        """
        pass
    
    def _generate_filename(
        self, 
        intel: 'WebsiteIntelligence', 
        extension: str = 'pdf'
    ) -> str:
        """Generate a filename for the report."""
        safe_domain = intel.domain.replace('.', '_').replace('/', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.REPORT_TYPE}_report_{safe_domain}_{timestamp}.{extension}"
    
    def save_text_report(
        self,
        intel: 'WebsiteIntelligence',
        filename: Optional[str] = None
    ) -> Path:
        """
        Save report as plain text file.
        
        Args:
            intel: WebsiteIntelligence object
            filename: Output filename
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            filename = self._generate_filename(intel, 'txt')
        
        output_path = self.output_dir / filename
        content = self.get_text_content(intel)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
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
    
    def _get_status_symbol(self, condition: bool) -> str:
        """Get status symbol for boolean condition."""
        return '✓' if condition else '✗'
    
    def _format_header(self, title: str, width: int = 60) -> str:
        """Format a section header."""
        return f"\n{'=' * width}\n{title.center(width)}\n{'=' * width}\n"
    
    def _format_subheader(self, title: str, width: int = 60) -> str:
        """Format a subsection header."""
        return f"\n{title}\n{'-' * len(title)}\n"