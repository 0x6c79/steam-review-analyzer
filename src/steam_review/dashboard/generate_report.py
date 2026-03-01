#!/usr/bin/env python3
"""
Generate PDF Report from Analysis
"""
import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def generate_pdf_report(csv_file, output_file=None):
    """Generate a PDF report from CSV analysis"""
    
    if output_file is None:
        output_file = csv_file.replace('.csv', '_report.pdf')
    
    # Load data
    df = pd.read_csv(csv_file)
    app_name = os.path.basename(csv_file).split('_reviews')[0]
    
    # Convert voted_up to boolean if stored as string
    if 'voted_up' in df.columns:
        if df['voted_up'].dtype == 'object':
            df['voted_up'] = df['voted_up'].map({'True': True, 'False': False})
    
    # Create PDF
    doc = SimpleDocTemplate(output_file, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                fontSize=24, spaceAfter=30, alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                  fontSize=16, spaceAfter=12, spaceBefore=20)
    normal_style = styles['Normal']
    
    story = []
    
    # Title
    story.append(Paragraph(f"Steam Review Analysis Report", title_style))
    story.append(Paragraph(f"Game: {app_name}", styles['Heading3']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Overview
    story.append(Paragraph("Overview", heading_style))
    
    total = len(df)
    positive = df['voted_up'].sum() if 'voted_up' in df.columns else 0
    negative = total - positive
    positive_rate = positive / total * 100 if total > 0 else 0
    
    overview_data = [
        ['Metric', 'Value'],
        ['Total Reviews', str(total)],
        ['Positive Reviews', str(int(positive))],
        ['Negative Reviews', str(int(negative))],
        ['Positive Rate', f"{positive_rate:.1f}%"],
    ]
    
    overview_table = Table(overview_data, colWidths=[2.5*inch, 2*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(overview_table)
    
    # Language distribution
    if 'language' in df.columns:
        story.append(Paragraph("Language Distribution", heading_style))
        
        lang_counts = df['language'].value_counts().head(10)
        
        lang_data = [['Language', 'Count', 'Percentage']]
        for lang, count in lang_counts.items():
            pct = count / total * 100
            lang_data.append([lang, str(count), f"{pct:.1f}%"])
        
        lang_table = Table(lang_data, colWidths=[2*inch, 1.25*inch, 1.25*inch])
        lang_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(lang_table)
    
    # Review length stats
    if 'review' in df.columns:
        story.append(Paragraph("Review Length Statistics", heading_style))
        
        df['review_length'] = df['review'].astype(str).str.len()
        
        length_stats = [
            ['Metric', 'Value'],
            ['Average Length', f"{df['review_length'].mean():.0f} characters"],
            ['Max Length', f"{df['review_length'].max()} characters"],
            ['Min Length', f"{df['review_length'].min()} characters"],
        ]
        
        length_table = Table(length_stats, colWidths=[2*inch, 3*inch])
        length_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(length_table)
    
    # Sample reviews
    story.append(Paragraph("Sample Reviews", heading_style))
    
    if 'review' in df.columns and 'voted_up' in df.columns:
        positive_samples = df[df['voted_up']].head(3)
        negative_samples = df[~df['voted_up']].head(3)
        
        story.append(Paragraph("Positive Reviews", styles['Heading4']))
        for _, row in positive_samples.iterrows():
            review_text = str(row['review'])[:200] + "..." if len(str(row['review'])) > 200 else str(row['review'])
            story.append(Paragraph(f"• {review_text}", normal_style))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph("Negative Reviews", styles['Heading4']))
        for _, row in negative_samples.iterrows():
            review_text = str(row['review'])[:200] + "..." if len(str(row['review'])) > 200 else str(row['review'])
            story.append(Paragraph(f"• {review_text}", normal_style))
            story.append(Spacer(1, 6))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Generated by Steam Review Analyzer", 
                         ParagraphStyle('Footer', parent=normal_style, 
                                       fontSize=8, textColor=colors.grey)))
    
    # Build PDF
    doc.build(story)
    print(f"PDF report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file', help='CSV file to process')
    parser.add_argument('--output', '-o', help='Output PDF file')
    args = parser.parse_args()
    
    generate_pdf_report(args.csv_file, args.output)
