"""
PDF export functionality for Steam review reports.
Generates professional PDF reports with charts and statistics.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from io import BytesIO
import pandas as pd

project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate professional PDF reports from review data."""
    
    @staticmethod
    def is_available() -> bool:
        """Check if reportlab is available."""
        return REPORTLAB_AVAILABLE
    
    @staticmethod
    def create_report(
        df: pd.DataFrame,
        stats: Dict[str, Any],
        app_id: Optional[str] = None,
        title: str = "Steam Review Report",
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Create a PDF report from review data.
        
        Args:
            df: DataFrame with review data
            stats: Dictionary of statistics
            app_id: Optional app ID for naming
            title: Report title
            output_path: Optional file path to save (if None, returns bytes)
        
        Returns:
            PDF bytes if output_path is None, else None
        """
        if not REPORTLAB_AVAILABLE:
            logger.warning("reportlab not available, PDF export disabled")
            return None
        
        try:
            # Create PDF document
            buffer = BytesIO() if output_path is None else None
            doc_path = output_path or "temp.pdf"
            
            doc = SimpleDocTemplate(
                doc_path if output_path else buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f77b4'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=12,
            )
            
            # Title
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.3 * inch))
            
            # Generate timestamp
            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            elements.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))
            
            # Statistics Section
            elements.append(Paragraph("📊 Summary Statistics", heading_style))
            
            stat_data = [
                ['Metric', 'Value'],
                ['Total Reviews', f"{stats.get('total', 0):,}"],
                ['Positive Reviews', f"{stats.get('positive', 0):,}"],
                ['Negative Reviews', f"{stats.get('negative', 0):,}"],
                ['Positive Rate', f"{(stats.get('positive', 0) / max(stats.get('total', 1), 1) * 100):.1f}%"],
            ]
            
            stat_table = Table(stat_data, colWidths=[3*inch, 2*inch])
            stat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(stat_table)
            elements.append(Spacer(1, 0.2 * inch))
            
            # Data Quality Section
            elements.append(Paragraph("📈 Data Quality", heading_style))
            
            quality_data = [
                ['Metric', 'Value'],
                ['Total Records', f"{len(df):,}"],
                ['Columns', f"{len(df.columns)}"],
                ['Missing Values', f"{df.isnull().sum().sum()}"],
                ['Date Span', f"{(df['timestamp_created'].max() - df['timestamp_created'].min()).days} days"] if 'timestamp_created' in df.columns else ['Date Span', 'N/A'],
            ]
            
            quality_table = Table(quality_data, colWidths=[3*inch, 2*inch])
            quality_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(quality_table)
            elements.append(Spacer(1, 0.2 * inch))
            
            # Top Reviews Section
            elements.append(Paragraph("⭐ Top Helpful Reviews (Sample)", heading_style))
            
            # Get top 5 reviews sorted by votes
            top_reviews = df.nlargest(5, 'voted_up')[['author_num_reviews', 'playtime_forever', 'voted_up']].head(5)
            
            review_data = [['Author Reviews', 'Playtime (hrs)', 'Helpful Votes']]
            for idx, row in top_reviews.iterrows():
                review_data.append([
                    f"{int(row['author_num_reviews'])}",
                    f"{int(row['playtime_forever'])}",
                    f"{int(row['voted_up'])}",
                ])
            
            review_table = Table(review_data, colWidths=[2*inch, 2*inch, 1.5*inch])
            review_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(review_table)
            elements.append(Spacer(1, 0.3 * inch))
            
            # Build PDF
            if output_path:
                doc.build(elements)
                logger.info(f"PDF report saved to {output_path}")
                return None
            else:
                doc.build(elements)
                pdf_bytes = buffer.getvalue()
                buffer.close()
                logger.info(f"PDF report generated ({len(pdf_bytes)} bytes)")
                return pdf_bytes
        
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return None
    
    @staticmethod
    def create_summary_report(
        stats: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Create a quick summary PDF report with just statistics.
        
        Args:
            stats: Dictionary of statistics
            metadata: Optional metadata
            output_path: Optional file path to save
        
        Returns:
            PDF bytes or None
        """
        if not REPORTLAB_AVAILABLE:
            return None
        
        try:
            buffer = BytesIO() if output_path is None else None
            doc_path = output_path or "summary.pdf"
            
            doc = SimpleDocTemplate(
                doc_path if output_path else buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=colors.HexColor('#e74c3c'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            
            elements.append(Paragraph("Steam Review Analytics Summary", title_style))
            elements.append(Spacer(1, 0.5 * inch))
            
            # Summary table
            summary_data = [
                ['Total Reviews', f"{stats.get('total', 0):,}"],
                ['Positive Reviews', f"{stats.get('positive', 0):,}"],
                ['Negative Reviews', f"{stats.get('negative', 0):,}"],
                ['Positive Rate', f"{(stats.get('positive', 0) / max(stats.get('total', 1), 1) * 100):.1f}%"],
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('PADDING', (0, 0), (-1, -1), 15),
                ('GRID', (0, 0), (-1, -1), 2, colors.black),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.lightblue, colors.white]),
            ]))
            
            elements.append(summary_table)
            
            if output_path:
                doc.build(elements)
                return None
            else:
                doc.build(elements)
                pdf_bytes = buffer.getvalue()
                buffer.close()
                return pdf_bytes
        
        except Exception as e:
            logger.error(f"Error creating summary PDF: {e}")
            return None
