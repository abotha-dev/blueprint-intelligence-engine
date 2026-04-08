"""
PDF Report Generator for Takeoff.ai

Generates professional, print-friendly PDF estimates for construction projects.
"""

from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class PDFReportGenerator:
    """Generates professional, print-friendly PDF reports for construction estimates."""

    # Brand colors — blue palette matching the web app
    BRAND_BLUE = colors.HexColor('#4F6DF5')
    BRAND_BLUE_DARK = colors.HexColor('#3B50C4')
    BRAND_BLUE_LIGHT = colors.HexColor('#EEF1FE')    # Very light tint for table rows (prints well)
    BRAND_BLUE_MID = colors.HexColor('#D4DBFC')       # Medium tint for header rows

    # Neutrals — high contrast for print
    TEXT_PRIMARY = colors.HexColor('#111827')
    TEXT_SECONDARY = colors.HexColor('#374151')
    TEXT_MUTED = colors.HexColor('#6B7280')
    BORDER = colors.HexColor('#D1D5DB')
    BORDER_LIGHT = colors.HexColor('#E5E7EB')
    ROW_ALT = colors.HexColor('#F9FAFB')
    WHITE = colors.white

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        self.styles.add(ParagraphStyle(
            name='BrandName',
            fontSize=22,
            fontName='Helvetica-Bold',
            textColor=self.BRAND_BLUE,
            spaceAfter=2,
            leading=26,
        ))

        self.styles.add(ParagraphStyle(
            name='BrandTagline',
            fontSize=9,
            fontName='Helvetica',
            textColor=self.TEXT_MUTED,
            spaceAfter=0,
            leading=12,
        ))

        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            fontName='Helvetica-Bold',
            textColor=self.TEXT_PRIMARY,
            spaceBefore=0,
            spaceAfter=4,
            leading=24,
        ))

        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            fontSize=10,
            fontName='Helvetica',
            textColor=self.TEXT_MUTED,
            spaceAfter=16,
            leading=14,
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            fontSize=13,
            fontName='Helvetica-Bold',
            textColor=self.TEXT_PRIMARY,
            spaceBefore=22,
            spaceAfter=8,
            leading=16,
            borderPadding=(0, 0, 0, 4),
        ))

        self.styles.add(ParagraphStyle(
            name='SectionDesc',
            fontSize=9,
            fontName='Helvetica',
            textColor=self.TEXT_MUTED,
            spaceAfter=8,
            leading=12,
        ))

        self.styles.add(ParagraphStyle(
            name='ReportBody',
            fontSize=10,
            fontName='Helvetica',
            textColor=self.TEXT_SECONDARY,
            spaceAfter=4,
            leading=14,
        ))

        self.styles.add(ParagraphStyle(
            name='SmallText',
            fontSize=8,
            fontName='Helvetica',
            textColor=self.TEXT_MUTED,
            spaceAfter=3,
            leading=11,
        ))

        self.styles.add(ParagraphStyle(
            name='FooterText',
            fontSize=8,
            fontName='Helvetica',
            textColor=self.TEXT_MUTED,
            alignment=TA_CENTER,
            leading=11,
        ))

        self.styles.add(ParagraphStyle(
            name='GrandTotalLabel',
            fontSize=10,
            fontName='Helvetica',
            textColor=self.TEXT_MUTED,
            alignment=TA_RIGHT,
            leading=13,
        ))

        self.styles.add(ParagraphStyle(
            name='GrandTotalValue',
            fontSize=20,
            fontName='Helvetica-Bold',
            textColor=self.BRAND_BLUE,
            alignment=TA_RIGHT,
            leading=26,
        ))

    def _format_currency(self, value: float) -> str:
        """Format a number as USD currency."""
        return f"${value:,.2f}"

    def generate_report(
        self,
        project_name: str,
        rooms: List[Dict[str, Any]],
        materials: List[Dict[str, Any]],
        cost_breakdown: Dict[str, float],
        tier_comparisons: List[Dict[str, Any]],
        selected_tier: str = 'standard',
        quality_tier: str = 'standard',
        region: str = 'us_national',
        include_labor: bool = True,
        total_area: float = 0,
        contingency_percent: float = 10,
        filename: str = 'blueprint.jpg',
        labor_availability: str = 'average',
        structural_estimates: Optional[Dict[str, Any]] = None,
    ) -> BytesIO:
        """
        Generate a PDF report for the construction estimate.

        Returns: BytesIO buffer containing the PDF
        """
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        # Calculate combined grand total (interior + structural)
        interior_total = cost_breakdown.get('grand_total', 0)
        structural_total = structural_estimates.get('grand_total', 0) if structural_estimates else 0
        combined_grand_total = interior_total + structural_total

        story = []

        # -- Header --
        story.extend(self._build_header(project_name, filename, selected_tier))

        # -- Grand-total callout (combined total) --
        story.extend(self._build_grand_total_box(
            grand_total=combined_grand_total,
            room_count=len(rooms),
            total_area=total_area,
            selected_tier=selected_tier,
        ))

        # -- Analysis Settings --
        story.extend(self._build_analysis_settings(
            quality_tier=quality_tier,
            region=region,
            include_labor=include_labor,
            contingency_percent=contingency_percent,
            labor_availability=labor_availability,
        ))

        # -- Room Breakdown --
        story.extend(self._build_room_breakdown(rooms))

        # -- Cost Estimate Table (interior finishes) --
        story.extend(self._build_cost_table(
            materials, cost_breakdown, contingency_percent,
            structural_total=structural_total,
            combined_grand_total=combined_grand_total,
        ))

        # -- Structural Shell Estimate --
        if structural_estimates and structural_total > 0:
            story.extend(self._build_structural_estimates(structural_estimates))

        # -- Quality Tier Comparison --
        story.extend(self._build_tier_comparison(tier_comparisons, selected_tier))

        # -- Disclaimer & Footer --
        story.extend(self._build_footer())

        # Build with page-number footer
        doc.build(story, onFirstPage=self._page_footer, onLaterPages=self._page_footer)
        buffer.seek(0)
        return buffer

    # ------------------------------------------------------------------
    # Page-level callback: adds page number footer on every page
    # ------------------------------------------------------------------
    def _page_footer(self, canvas, doc):
        """Draw page number at bottom-center of every page."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.TEXT_MUTED)
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(
            doc.pagesize[0] / 2.0,
            0.4 * inch,
            f"Page {page_num}"
        )
        canvas.restoreState()

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_header(self, project_name: str, filename: str, selected_tier: str) -> List:
        """Build the branded report header."""
        elements = []

        # Two-column header: brand on left, date on right
        tier_label = selected_tier.capitalize()
        date_str = datetime.now().strftime("%B %d, %Y")

        left_col = [
            [Paragraph('<b>Takeoff.ai</b>', self.styles['BrandName'])],
            [Paragraph('AI-Powered Construction Estimator', self.styles['BrandTagline'])],
        ]
        left_table = Table(left_col, colWidths=[4 * inch])
        left_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        right_col = [
            [Paragraph(f'<font size="9" color="#6B7280">{date_str}</font>', self.styles['ReportBody'])],
            [Paragraph(f'<font size="9" color="#6B7280">{tier_label} Tier</font>', self.styles['ReportBody'])],
        ]
        right_table = Table(right_col, colWidths=[3 * inch])
        right_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        header_table = Table([[left_table, right_table]], colWidths=[4 * inch, 3 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # Blue accent line
        elements.append(HRFlowable(
            width="100%", thickness=2, color=self.BRAND_BLUE, spaceAfter=14
        ))

        # Title and project info
        elements.append(Paragraph('Construction Cost Estimate', self.styles['ReportTitle']))
        elements.append(Paragraph(
            f'{project_name}  ·  Source: {filename}',
            self.styles['ReportSubtitle'],
        ))

        return elements

    def _build_grand_total_box(
        self,
        grand_total: float,
        room_count: int,
        total_area: float,
        selected_tier: str,
    ) -> List:
        """Build a prominent grand-total callout box with a border — no heavy fill so it prints cleanly."""
        elements = []

        tier_label = selected_tier.capitalize()
        meta_text = f"{room_count} room{'s' if room_count != 1 else ''}  ·  {total_area:,.0f} sq ft  ·  {tier_label} tier"

        box_data = [[
            Paragraph(f'<font size="9" color="#6B7280">Estimated Grand Total</font>', self.styles['ReportBody']),
            '',
        ], [
            Paragraph(f'<b>{self._format_currency(grand_total)}</b>', ParagraphStyle(
                name='_gt_val',
                fontSize=22,
                fontName='Helvetica-Bold',
                textColor=self.BRAND_BLUE,
                leading=28,
            )),
            Paragraph(f'<font size="9" color="#6B7280">{meta_text}</font>', ParagraphStyle(
                name='_gt_meta',
                fontSize=9,
                fontName='Helvetica',
                textColor=self.TEXT_MUTED,
                alignment=TA_RIGHT,
                leading=12,
            )),
        ]]

        box = Table(box_data, colWidths=[3.5 * inch, 3.5 * inch])
        box.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 0), (1, 0)),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
            ('BOX', (0, 0), (-1, -1), 1.5, self.BRAND_BLUE),
            ('BACKGROUND', (0, 0), (-1, -1), self.BRAND_BLUE_LIGHT),
        ]))

        elements.append(box)
        elements.append(Spacer(1, 18))

        return elements

    def _section_heading(self, title: str, description: str = '') -> List:
        """Return a section heading with optional description."""
        elements = []

        # Blue left-accent bar via a small table
        accent_data = [[
            '',
            Paragraph(f'<b>{title}</b>', self.styles['SectionHeading']),
        ]]
        accent = Table(accent_data, colWidths=[4, 6.9 * inch])
        accent.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.BRAND_BLUE),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
            ('TOPPADDING', (0, 0), (0, 0), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 0),
            ('LEFTPADDING', (1, 0), (1, 0), 8),
            ('TOPPADDING', (1, 0), (1, 0), 0),
            ('BOTTOMPADDING', (1, 0), (1, 0), 0),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(Spacer(1, 16))
        elements.append(accent)

        if description:
            elements.append(Paragraph(description, self.styles['SectionDesc']))

        elements.append(Spacer(1, 4))
        return elements

    def _build_analysis_settings(
        self,
        quality_tier: str,
        region: str,
        include_labor: bool,
        contingency_percent: float,
        labor_availability: str,
    ) -> List:
        """Build the analysis settings as a compact two-column grid."""
        elements = self._section_heading('Analysis Settings', 'Parameters used for this estimate.')

        tier_labels = {'budget': 'Budget', 'standard': 'Standard', 'premium': 'Premium', 'luxury': 'Luxury'}
        labor_labels = {'low': 'Low (Shortage +15%)', 'average': 'Average', 'high': 'High (Surplus -10%)'}

        def fmt_region(r):
            if not r.startswith('us_'):
                return r
            m = {
                'us_national': 'National Average', 'us_northeast': 'Northeast',
                'us_southeast': 'Southeast', 'us_midwest': 'Midwest',
                'us_southwest': 'Southwest', 'us_west': 'West',
            }
            return m.get(r, r)

        # Two-column key-value pairs
        pairs = [
            ('Quality Tier', tier_labels.get(quality_tier, quality_tier.capitalize())),
            ('Location', fmt_region(region)),
            ('Labor Availability', labor_labels.get(labor_availability, labor_availability.capitalize())),
            ('Labor Costs', 'Included' if include_labor else 'Not Included'),
            ('Contingency', f'{contingency_percent:.0f}%'),
        ]

        # Lay out as a 2-col × N-row grid
        rows = []
        for i in range(0, len(pairs), 2):
            left_label, left_val = pairs[i]
            row = [
                Paragraph(f'<font size="8" color="#6B7280">{left_label}</font>', self.styles['SmallText']),
                Paragraph(f'<font size="9"><b>{left_val}</b></font>', self.styles['ReportBody']),
            ]
            if i + 1 < len(pairs):
                right_label, right_val = pairs[i + 1]
                row.extend([
                    Paragraph(f'<font size="8" color="#6B7280">{right_label}</font>', self.styles['SmallText']),
                    Paragraph(f'<font size="9"><b>{right_val}</b></font>', self.styles['ReportBody']),
                ])
            else:
                row.extend(['', ''])
            rows.append(row)

        t = Table(rows, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, self.BORDER_LIGHT),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, self.BORDER_LIGHT),
        ]))

        elements.append(t)
        elements.append(Spacer(1, 8))
        return elements

    def _build_room_breakdown(self, rooms: List[Dict[str, Any]]) -> List:
        """Build the room breakdown table."""
        elements = self._section_heading(
            'Room Breakdown',
            f'{len(rooms)} room{"s" if len(rooms) != 1 else ""} detected from blueprint analysis.'
        )

        header = ['Room', 'Dimensions', 'Area (sq ft)', 'Confidence']
        data = [header]

        for room in rooms:
            dims = room.get('dimensions', {})
            w = dims.get('width', 0)
            l = dims.get('length', 0)

            unit = room.get('unit', 'imperial')
            if unit == 'metric' and (w > 0 or l > 0):
                w *= 3.28084
                l *= 3.28084

            dim_str = f"{l:.1f}' x {w:.1f}'" if (w > 0 and l > 0) else 'Estimated'

            area = room.get('area', 0)
            if unit == 'metric' and area > 0:
                area *= 10.7639

            conf = room.get('confidence', 0.5)
            if conf >= 0.8:
                conf_str = 'High'
            elif conf >= 0.6:
                conf_str = 'Medium'
            else:
                conf_str = 'Low'

            data.append([
                room.get('name', 'Unknown'),
                dim_str,
                f"{area:,.0f}",
                conf_str,
            ])

        col_widths = [2.5 * inch, 1.6 * inch, 1.2 * inch, 0.95 * inch]
        table = Table(data, colWidths=col_widths)

        style_cmds = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.BRAND_BLUE_MID),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.TEXT_PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            # Body rows
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.TEXT_SECONDARY),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            # Alignment
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            # Alternating row backgrounds
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.WHITE, self.ROW_ALT]),
            # Borders: outer box + horizontal lines between rows
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, self.BORDER),
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, self.BORDER_LIGHT),
        ]

        table.setStyle(TableStyle(style_cmds))
        elements.append(table)
        elements.append(Spacer(1, 8))
        return elements

    def _build_cost_table(
        self,
        materials: List[Dict[str, Any]],
        cost_breakdown: Dict[str, float],
        contingency_percent: float,
        structural_total: float = 0,
        combined_grand_total: float = 0,
    ) -> List:
        """Build the itemized cost estimate table with category grouping and summary totals."""
        elements = self._section_heading(
            'Cost Estimate',
            'Itemized material and labor costs grouped by category.'
        )

        # Group materials by category
        grouped: Dict[str, List[Dict]] = {}
        for item in materials:
            cat = item.get('category', 'Other')
            grouped.setdefault(cat, []).append(item)

        header = ['Item', 'Qty', 'Unit Cost', 'Materials', 'Labor', 'Total']
        data = [header]
        category_rows = []

        for category, items in grouped.items():
            # Category separator row
            cat_row_idx = len(data)
            category_rows.append(cat_row_idx)
            data.append([category.upper(), '', '', '', '', ''])

            for item in items:
                data.append([
                    f"  {item.get('name', 'Unknown')}",
                    f"{item.get('quantity', 0)} {item.get('unit', '')}",
                    self._format_currency(item.get('unit_cost', 0)),
                    self._format_currency(item.get('material_cost', 0)),
                    self._format_currency(item.get('labor_cost', 0)),
                    self._format_currency(item.get('total_cost', 0)),
                ])

        col_widths = [2.2 * inch, 0.85 * inch, 0.85 * inch, 0.95 * inch, 0.95 * inch, 1.0 * inch]
        table = Table(data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.BRAND_BLUE_MID),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.TEXT_PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            ('ALIGN', (1, 0), (-1, 0), 'RIGHT'),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.TEXT_SECONDARY),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            # Borders
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, self.BORDER),
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, self.BORDER_LIGHT),
        ]

        # Category separator rows: light blue bg, bold, span full width
        for idx in category_rows:
            style_cmds.extend([
                ('BACKGROUND', (0, idx), (-1, idx), self.BRAND_BLUE_LIGHT),
                ('FONTNAME', (0, idx), (0, idx), 'Helvetica-Bold'),
                ('FONTSIZE', (0, idx), (0, idx), 8),
                ('TEXTCOLOR', (0, idx), (0, idx), self.TEXT_PRIMARY),
                ('SPAN', (0, idx), (-1, idx)),
                ('TOPPADDING', (0, idx), (-1, idx), 5),
                ('BOTTOMPADDING', (0, idx), (-1, idx), 5),
                ('LINEBELOW', (0, idx), (-1, idx), 0.5, self.BORDER),
            ])

        table.setStyle(TableStyle(style_cmds))
        elements.append(table)

        # ---- Summary totals (right-aligned) ----
        elements.append(Spacer(1, 10))

        materials_sub = cost_breakdown.get('materials_subtotal', 0)
        labor_sub = cost_breakdown.get('labor_subtotal', 0)
        subtotal = cost_breakdown.get('subtotal', 0)
        contingency = cost_breakdown.get('contingency_amount', 0)
        interior_total = cost_breakdown.get('grand_total', 0)

        summary_data = [
            ['Materials Subtotal', self._format_currency(materials_sub)],
            ['Labor Subtotal', self._format_currency(labor_sub)],
            ['Subtotal', self._format_currency(subtotal)],
            [f'Contingency ({contingency_percent:.0f}%)', self._format_currency(contingency)],
        ]

        if structural_total > 0:
            summary_data.append(['Interior Finishes Total', self._format_currency(interior_total)])
            summary_data.append(['Structural Shell', self._format_currency(structural_total)])
            summary_data.append(['Grand Total', self._format_currency(combined_grand_total)])
        else:
            summary_data.append(['Grand Total', self._format_currency(interior_total)])

        summary = Table(summary_data, colWidths=[2 * inch, 1.5 * inch])

        summary_style = [
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_SECONDARY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            # Subtotal line
            ('LINEABOVE', (0, 2), (-1, 2), 0.5, self.BORDER_LIGHT),
            # Grand total emphasis
            ('LINEABOVE', (0, -1), (-1, -1), 1, self.BORDER),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (1, -1), (1, -1), self.BRAND_BLUE),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ]
        summary.setStyle(TableStyle(summary_style))

        # Right-align the summary block
        wrapper = Table([[summary]], colWidths=[7 * inch])
        wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'RIGHT')]))
        elements.append(wrapper)
        elements.append(Spacer(1, 12))
        return elements

    def _build_structural_estimates(self, structural: Dict[str, Any]) -> List:
        """Build the structural shell estimate section (framing, foundation, roofing)."""
        elements = self._section_heading(
            'Structural Shell Estimate',
            'Framing, foundation, and roofing costs based on NAHB 2024 benchmarks.'
        )

        sections = [
            ('Framing', 'Studs, plates, headers', structural.get('framing', {})),
            ('Foundation', 'Slab-on-grade', structural.get('foundation', {})),
            ('Roofing', 'Gable roof, 4/12 pitch', structural.get('roofing', {})),
        ]

        # Build a table for each structural sub-section side by side
        for section_name, subtitle, detail in sections:
            line_items = detail.get('line_items', {})
            total_mat = detail.get('total_material', 0)
            total_lab = detail.get('total_labor', 0)
            grand = detail.get('grand_total', 0)

            header = [f'{section_name}', '']
            data = [header]
            data.append([Paragraph(f'<font size="7" color="#6B7280"><i>{subtitle}</i></font>', self.styles['SmallText']), ''])

            for key, item in line_items.items():
                label = key.replace('_', ' ').capitalize()
                cost = item.get('total_cost', 0) if isinstance(item, dict) else 0
                data.append([f'  {label}', self._format_currency(cost)])

            data.append(['Materials', self._format_currency(total_mat)])
            data.append(['Labor', self._format_currency(total_lab)])
            data.append(['Total', self._format_currency(grand)])

            t = Table(data, colWidths=[2.5 * inch, 1.5 * inch])
            last = len(data) - 1
            t.setStyle(TableStyle([
                # Header
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_SECONDARY),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                # Total row
                ('LINEABOVE', (0, last), (-1, last), 0.5, self.BORDER),
                ('FONTNAME', (0, last), (-1, last), 'Helvetica-Bold'),
                # Box
                ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER_LIGHT),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 6))

        # Structural grand total
        struct_total = structural.get('grand_total', 0)
        total_row = Table(
            [['Structural Shell Total', self._format_currency(struct_total)]],
            colWidths=[2.5 * inch, 1.5 * inch],
        )
        total_row.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, 0), self.TEXT_PRIMARY),
            ('TEXTCOLOR', (1, 0), (1, 0), self.BRAND_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, 0), (-1, 0), 1, self.BORDER),
        ]))

        wrapper = Table([[total_row]], colWidths=[7 * inch])
        wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'RIGHT')]))
        elements.append(wrapper)
        elements.append(Spacer(1, 12))

        return elements

    def _build_tier_comparison(
        self,
        tier_comparisons: List[Dict[str, Any]],
        selected_tier: str,
    ) -> List:
        """Build the quality tier comparison table."""
        elements = self._section_heading(
            'Quality Tier Comparison',
            'Estimated totals at different quality levels. Your selected tier is highlighted.'
        )

        tier_info = {
            'budget': ('Budget', 'Builder-grade materials, functional finishes'),
            'standard': ('Standard', 'Quality mid-range materials and finishes'),
            'premium': ('Premium', 'High-end finishes and upgraded fixtures'),
            'luxury': ('Luxury', 'Top-tier materials and custom finishes'),
        }

        header = ['Tier', 'Description', 'Estimated Total']
        data = [header]

        selected_row = None
        for i, tier in enumerate(tier_comparisons):
            tier_name = tier.get('tier', 'standard')
            label, desc = tier_info.get(tier_name, (tier_name.capitalize(), ''))
            total = tier.get('grand_total', 0)

            if tier_name == selected_tier:
                selected_row = i + 1
                label = f">>> {label}"

            data.append([label, desc, self._format_currency(total)])

        col_widths = [1.4 * inch, 3.0 * inch, 1.6 * inch]
        table = Table(data, colWidths=col_widths)

        style_cmds = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.BRAND_BLUE_MID),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.TEXT_PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.TEXT_SECONDARY),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            # Borders
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, self.BORDER),
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, self.BORDER_LIGHT),
        ]

        # Highlight the selected tier row
        if selected_row is not None:
            style_cmds.extend([
                ('BACKGROUND', (0, selected_row), (-1, selected_row), self.BRAND_BLUE_LIGHT),
                ('FONTNAME', (0, selected_row), (-1, selected_row), 'Helvetica-Bold'),
                ('TEXTCOLOR', (2, selected_row), (2, selected_row), self.BRAND_BLUE),
            ])

        table.setStyle(TableStyle(style_cmds))
        elements.append(table)
        elements.append(Spacer(1, 20))
        return elements

    def _build_footer(self) -> List:
        """Build the report footer with disclaimer."""
        elements = []

        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(
            width="100%", thickness=0.75, color=self.BORDER, spaceAfter=12
        ))

        disclaimer = (
            "<b>Disclaimer:</b> This estimate is generated by AI-powered analysis and is "
            "intended for planning purposes only. Actual costs may vary based on local labor "
            "rates, material availability, site conditions, and other factors. We recommend "
            "obtaining quotes from licensed contractors before making final decisions. This "
            "estimate does not include permits, design fees, or unforeseen conditions."
        )
        elements.append(Paragraph(disclaimer, self.styles['SmallText']))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(
            'Generated by Takeoff.ai  —  AI-Powered Construction Estimator',
            self.styles['FooterText'],
        ))
        elements.append(Paragraph(
            'https://mytakeoff.ai',
            self.styles['FooterText'],
        ))

        return elements
