#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
generate_report.py
CSE/PC/B/S/314 Computer Networks Lab - Assignment 3
Comprehensive Formal Laboratory Report Generator in PDF format
using ReportLab with publication-grade typography, high-resolution LaTeX
mathematical formula cards, embedded architectural & FSM flowcharts,
detailed C implementation code snippets, empirical benchmark curves,
and exhaustive Theoretical vs. Empirical "What & Why" analysis.

Author: Akshay Gupta (Roll: 002410501049, Section A2, BCSE III)
Department of Computer Science & Engineering, Jadavpur University
==============================================================================
"""

import os
import sys
from pathlib import Path
from PIL import Image as PILImage

BASE_DIR = Path(__file__).resolve().parent
LIBS_DIR = BASE_DIR / "libs"
if str(LIBS_DIR) not in sys.path:
    sys.path.insert(0, str(LIBS_DIR))

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

RESULTS_DIR = BASE_DIR / "results"
CHARTS_DIR = RESULTS_DIR / "charts"
MATH_DIR = CHARTS_DIR / "math"
OUTPUT_PDF = BASE_DIR / "AKSHAY_GUPTA_002410501049_A3.pdf"

# ------------------------------------------------------------------------------
# Numbered Canvas for Running Headers and Page Numbers (Page X of Y)
# ------------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        print(f"[+] Total pages rendered in PDF: {num_pages}")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running header/footer on title/cover page

        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#555555"))

        # Header
        self.drawString(54, 804, "Jadavpur University | CSMA MAC Protocols & Collision Detection")
        self.setStrokeColor(colors.HexColor("#D0D0D0"))
        self.setLineWidth(0.5)
        self.line(54, 798, 541, 798)

        # Footer
        self.line(54, 46, 541, 46)
        self.drawString(54, 33, "Akshay Gupta (Roll: 002410501049) | Section A2 | BCSE III")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(541, 33, page_str)
        self.restoreState()

# ------------------------------------------------------------------------------
# Helper Functions for Image Embedding with Exact Aspect Ratio Preservation
# ------------------------------------------------------------------------------
def embed_chart(filename, max_width=485, max_height=275, caption=None, story=None, style_caption=None):
    img_path = CHARTS_DIR / filename
    if not img_path.exists():
        print(f"[-] Warning: Image not found: {img_path}")
        return
    im = PILImage.open(img_path)
    aspect = im.size[0] / im.size[1]
    w = max_width
    h = w / aspect
    if h > max_height:
        h = max_height
        w = h * aspect
    story.append(Image(str(img_path), width=w, height=h))
    if caption:
        story.append(Paragraph(f"<i>{caption}</i>", style_caption))
    story.append(Spacer(1, 4))

def embed_math_card(filename, max_width=485, max_height=65, caption=None, story=None, style_caption=None):
    img_path = MATH_DIR / filename
    if not img_path.exists():
        print(f"[-] Warning: Math card not found: {img_path}")
        return
    im = PILImage.open(img_path)
    aspect = im.size[0] / im.size[1]
    w = max_width
    h = w / aspect
    if h > max_height:
        h = max_height
        w = h * aspect
    story.append(Image(str(img_path), width=w, height=h))
    if caption:
        story.append(Paragraph(f"<i>{caption}</i>", style_caption))
    story.append(Spacer(1, 3))

def embed_code_box(title, code_str, story, style_code, width=485):
    header = Paragraph(f"<b>C Implementation: {title}</b>",
                       ParagraphStyle('CHeader', fontName='Helvetica-Bold', fontSize=10.5, leading=13.0, textColor=colors.HexColor('#1B4F72')))
    body = Paragraph(code_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code)
    t = Table([[header], [body]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EAEDED')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8F9F9')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#BDC3C7')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

# ------------------------------------------------------------------------------
# Main Report Generation Logic
# ------------------------------------------------------------------------------
def build_pdf_report():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    style_cover_title = ParagraphStyle(
        'CoverTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=22.0, leading=27.0, alignment=1, textColor=colors.HexColor('#900C3F')
    )
    style_cover_sub = ParagraphStyle(
        'CoverSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=13.5, leading=18.0, alignment=1, textColor=colors.HexColor('#2C3E50')
    )
    style_h1 = ParagraphStyle(
        'Heading1_Custom', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=16.5, leading=21.0, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor('#1B4F72')
    )
    style_h2 = ParagraphStyle(
        'Heading2_Custom', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=13.0, leading=17.0, spaceBefore=5, spaceAfter=3, textColor=colors.HexColor('#2874A6')
    )
    # 1.4x enlarged text for explanations (base ~8.6 pt * 1.4 = 12.0 pt, leading 16.5 pt)
    style_body = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=12.0, leading=16.5, alignment=4, spaceAfter=4.5, textColor=colors.HexColor('#222222')
    )
    style_bullet = ParagraphStyle(
        'Bullet_Custom', parent=style_body,
        leftIndent=16, firstLineIndent=-10, spaceAfter=3.5
    )
    style_explain = ParagraphStyle(
        'Explain_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.0, leading=13.5, alignment=4, spaceAfter=3.5, textColor=colors.HexColor('#222222')
    )
    style_code = ParagraphStyle(
        'Code_Custom', parent=styles['Normal'],
        fontName='Courier', fontSize=8.5, leading=11.2, textColor=colors.HexColor('#1C2833')
    )
    style_code_compact = ParagraphStyle(
        'CodeCompact_Custom', parent=styles['Normal'],
        fontName='Courier', fontSize=7.6, leading=9.6, textColor=colors.HexColor('#1C2833')
    )
    style_caption = ParagraphStyle(
        'Caption_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=14.0, alignment=1, spaceBefore=3.0, spaceAfter=5.0, textColor=colors.HexColor('#34495E')
    )
    style_table = ParagraphStyle(
        'Table_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.0, leading=12.0, textColor=colors.HexColor('#222222')
    )
    style_table_bold = ParagraphStyle(
        'TableBold_Custom', parent=style_table,
        fontName='Helvetica-Bold'
    )
    style_table_header = ParagraphStyle(
        'TableHeader_Custom', parent=style_table_bold,
        textColor=colors.white
    )
    style_table_code = ParagraphStyle(
        'TableCode_Custom', parent=styles['Normal'],
        fontName='Courier', fontSize=8.2, leading=10.8, textColor=colors.HexColor('#1C2833')
    )

    story = []

    # ==========================================================================
    # PAGE 1: COVER PAGE
    # ==========================================================================
    story.append(Spacer(1, 35))
    story.append(Paragraph("<b>COMPUTER NETWORKS LAB REPORT</b>", ParagraphStyle('ReportTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=26, leading=32, alignment=1, textColor=colors.HexColor('#1B4F72'))))
    story.append(Spacer(1, 10))
    story.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", ParagraphStyle('Dept', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14.5, leading=19, alignment=1, textColor=colors.HexColor('#2C3E50'))))
    story.append(Spacer(1, 26))

    # Assignment title prominently displayed below Department of Computer Science & Engineering
    story.append(Paragraph("<b>Assignment 3</b>", ParagraphStyle('Assign_Header', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=25, alignment=1, textColor=colors.HexColor('#900C3F'))))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Design and Implement Medium Access Control Mechanisms within a Simulated Network Environment using IEEE 802 Standards",
        ParagraphStyle('CO_Body', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, leading=18, alignment=1, textColor=colors.HexColor('#1B4F72'))
    ))
    story.append(Spacer(1, 28))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1B4F72'), spaceBefore=4, spaceAfter=28))

    style_meta_label = ParagraphStyle(
        'MetaLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=13.0, leading=17.5, textColor=colors.HexColor('#1B4F72')
    )
    style_meta_val = ParagraphStyle(
        'MetaVal', parent=styles['Normal'],
        fontName='Helvetica', fontSize=12.5, leading=17.0, textColor=colors.HexColor('#222222')
    )
    style_meta_val_bold = ParagraphStyle(
        'MetaValBold', parent=style_meta_val,
        fontName='Helvetica-Bold', textColor=colors.HexColor('#1B4F72')
    )

    meta_data = [
        [Paragraph("<b>Student Name:</b>", style_meta_label), Paragraph("<b>Akshay Gupta</b>", style_meta_val_bold)],
        [Paragraph("<b>Roll Number:</b>", style_meta_label), Paragraph("<b>002410501049</b>", style_meta_val_bold)],
        [Paragraph("<b>Class / Section:</b>", style_meta_label), Paragraph("BCSE III (3rd Year 1st Semester), Section A2", style_meta_val)],
        [Paragraph("<b>Department:</b>", style_meta_label), Paragraph("Department of Computer Science & Engineering", style_meta_val)],
    ]

    t_meta = Table(meta_data, colWidths=[145, 340])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9F9')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#1B4F72')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(t_meta)
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 2: EXECUTIVE SUMMARY & PROBLEM FORMULATION
    # ==========================================================================
    story.append(Paragraph("1. Executive Summary & Problem Formulation", style_h1))
    story.append(Paragraph(
        "In shared broadcast Local Area Networks (LANs), multiple autonomous stations contend for access to a common "
        "physical medium. Unlike point-to-point links governed by sliding-window flow control ARQ schemes (Stop-and-Wait, "
        "Go-Back-N, Selective Repeat), broadcast channels are inherently vulnerable to multi-access collisions: when two "
        "or more stations transmit concurrently, their electrical waveforms superimpose destructively, "
        "rendering all concurrent transmissions undecodable and corrupt.",
        style_body
    ))
    story.append(Paragraph(
        "While early multi-access schemes transmitted blindly without sensing the channel, <b>Carrier Sense Multiple Access (CSMA)</b> "
        "revolutionizes broadcast medium access through the foundational engineering principle of <i>'Listen Before Talk'</i> "
        "(Carrier Sensing). By sampling physical channel electrical energy prior to initiating a transmission, a station defers if an "
        "ongoing transmission is detected, dramatically shrinking the vulnerable period down to the physical propagation delay "
        "<i>&tau; = T<sub>p</sub></i> across the wire.",
        style_body
    ))
    story.append(Paragraph(
        "<b>Carrier Sense Multiple Access with Collision Detection (CSMA/CD)</b>, codified in the IEEE 802.3 Ethernet standard, "
        "further introduces <i>'Listen While Talk'</i>. Transmitting stations continuously sample the physical bus during transmission. "
        "Upon detecting concurrent energy (&ge; 2.0V), stations abort immediately, broadcast a 32-bit Jamming signal, and enter "
        "Truncated Binary Exponential Backoff (BEB), saving over 90% of the channel capacity that would otherwise be wasted transmitting doomed bits.",
        style_body
    ))
    story.append(Paragraph(
        "<b>1.1 Contention Dynamics & The Vulnerability Window:</b> "
        "Due to non-zero propagation delay <i>&tau; = T<sub>p</sub> = d / v</i>, carrier sensing cannot eliminate all collisions: "
        "a station sampling the wire during <i>[t<sub>0</sub>, t<sub>0</sub> + &tau;)</i> perceives the line as idle even after another station "
        "has commenced transmission. Different persistence strategies navigate this fundamental trade-off: Non-Persistent CSMA defers "
        "randomly to prevent collision cascades under heavy traffic; 1-Persistent CSMA eliminates access latency under light load; and "
        "p-Persistent CSMA balances throughput and delay across slotted intervals. This report presents the mathematical derivations, "
        "empirical benchmark evaluations, and concurrent multi-threaded POSIX implementation of these foundational MAC strategies.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 3: MULTI-THREADED SYSTEM ARCHITECTURE: BROADCAST MEDIUM (DIAGRAM 1)
    # ==========================================================================
    story.append(Paragraph("2. Multi-Threaded System Architecture: Shared Broadcast Medium & Synchronization", style_h1))
    story.append(Paragraph(
        "To rigorously emulate a physical multipoint broadcast bus architecture with high fidelity and minimal system overhead, our system employs "
        "concurrent POSIX threads (<code>pthreads</code>) executing over a thread-synchronized broadcast channel medium. Each station runs "
        "as an independent worker thread coordinating via fast POSIX mutexes and condition variables. "
        "Figure 2.1 illustrates the architectural topology and thread synchronization mechanisms:",
        style_body
    ))

    # Allot ample space to architecture diagram (almost full page)
    embed_chart("diagram_system_architecture.png", max_width=485, max_height=500,
                caption="Figure 2.1: Multi-Threaded System Architecture — Shared Broadcast Channel Medium & Concurrent Contending Station Threads (pthreads)",
                story=story, style_caption=style_caption)

    story.append(Paragraph(
        "<b>Architectural Takeaway:</b> The shared channel medium computes physical wire voltage superposition (0.0V Idle, 1.0V Busy, &ge;2.0V Collision) and models propagation delay <i>&tau; = T<sub>p</sub></i>, while station threads coordinate via POSIX mutexes and condition variables and independently record microsecond-level latency and backoff metrics.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 4: FRAME LAYOUT SPECIFICATION & MINIMUM FRAME SIZE CONSTRAINT
    # ==========================================================================
    story.append(Paragraph("3. IEEE 802.3 Frame Specification & Minimum Frame Size Constraint", style_h1))
    story.append(Paragraph(
        "Every frame transmitted across the TCP bus emulator complies with the IEEE 802.3 standard MAC frame structure, "
        "including 6-byte MAC addressing, type/length indication, sequence numbering, a 46-byte default payload, and a 4-byte CRC-32 Frame Check Sequence (FCS) trailer:",
        style_body
    ))

    frame_table_data = [
        [Paragraph("<b>Field Name</b>", style_table_bold), Paragraph("<b>Size</b>", style_table_bold), Paragraph("<b>Description / IEEE 802.3 Standard Semantics</b>", style_table_bold)],
        [Paragraph("Destination MAC", style_table), Paragraph("6 Bytes", style_table), Paragraph("Target interface identifier (Broadcast: <code>02:00:00:00:00:FF</code>)", style_table)],
        [Paragraph("Source MAC", style_table), Paragraph("6 Bytes", style_table), Paragraph("Transmitting station hardware identifier (<code>02:00:00:00:00:ID</code>)", style_table)],
        [Paragraph("Length Field", style_table), Paragraph("2 Bytes", style_table), Paragraph("Length of data payload in bytes (<code>uint16_t</code>, default 46 bytes)", style_table)],
        [Paragraph("Sequence Number", style_table), Paragraph("1 Byte", style_table), Paragraph("Station packet sequence counter modulo 256 for duplicate detection", style_table)],
        [Paragraph("Station ID", style_table), Paragraph("1 Byte", style_table), Paragraph("Contending station logical index (1..N)", style_table)],
        [Paragraph("Data Payload", style_table), Paragraph("46 Bytes", style_table), Paragraph("Application payload (pads frame to 64 bytes total: 6+6+2+1+1+46+2 = 64)", style_table)],
        [Paragraph("FCS Trailer", style_table), Paragraph("4 Bytes", style_table), Paragraph("IEEE 802.3 Cyclic Redundancy Check (CRC-32: polynomial <code>0xEDB88320</code>)", style_table)],
    ]
    t_frame = Table(frame_table_data, colWidths=[110, 60, 315])
    t_frame.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EAEDED')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#BDC3C7')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_frame)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>The Minimum Frame Size Constraint & 46-Byte Payload Padding:</b>", style_h2))
    story.append(Paragraph(
        "A critical engineering requirement of CSMA/CD is that a transmitting station <b>must remain actively transmitting until the round-trip propagation delay <i>2 T<sub>p</sub></i> has elapsed</b>. "
        "Consider the worst-case collision scenario across a bus of length <i>L</i> and propagation delay <i>T<sub>p</sub> = L / v</i>:<br/>"
        "1. Station A initiates transmission at time <i>t = 0</i>. The signal propagates toward Station B at velocity <i>v</i>.<br/>"
        "2. At time <i>t = T<sub>p</sub> - &epsilon;</i>, just before Station A's wavefront reaches Station B, Station B senses the medium. "
        "Because the wavefront has not yet arrived, Station B senses <code>IDLE</code> and begins transmitting.<br/>"
        "3. A destructive collision occurs almost immediately near Station B at <i>t = T<sub>p</sub></i>.<br/>"
        "4. The collision runt wavefront must now travel all the way back across the cable to Station A, arriving at time <i>t = 2 T<sub>p</sub> - &epsilon;</i>.",
        style_body
    ))
    story.append(Paragraph(
        "If Station A finishes transmitting before <i>t = 2 T<sub>p</sub></i>, it turns off its transceiver and switches to listening mode. "
        "Consequently, when the collision wavefront arrives, Station A fails to recognize that its own frame was destroyed, falsely assuming successful delivery! "
        "To guarantee that every station detects worst-case collisions while still actively transmitting, the frame transmission duration <i>T<sub>fr</sub></i> must satisfy:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b><i>T<sub>fr</sub> &ge; 2 T<sub>p</sub> &rArr; L<sub>min</sub> = 2 T<sub>p</sub> &times; Transmission Rate R</i></b><br/>"
        "For classical 10 Mbps Ethernet with maximum round-trip slot time <i>2 T<sub>p</sub> = 51.2 &mu;s</i>, this enforces a minimum frame length of "
        "<i>L<sub>min</sub> = 10 Mbps &times; 51.2 &mu;s = 512 bits = 64 Bytes</i>. Any payload smaller than 46 bytes is strictly padded with zeroes.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 5: CSMA PROTOCOL MECHANICS & COMPARATIVE FSM WORKFLOWS (DIAGRAM 2)
    # ==========================================================================
    story.append(Paragraph("4. CSMA Protocol Mechanics & Comparative FSM Workflows", style_h1))
    story.append(Paragraph(
        "We implemented four discrete CSMA persistence and collision recovery mechanisms inside <code>station/mac_strategies.c</code>. "
        "Figure 4.1 contrasts their operational Finite State Machines (FSMs), decision diamonds, and carrier sensing transitions:",
        style_body
    ))

    # Allot almost full page to the 4-panel FSM diagram
    embed_chart("diagram_csma_fsm_workflows.png", max_width=485, max_height=500,
                caption="Figure 4.1: Comparative Finite State Workflows for Non-Persistent, 1-Persistent, p-Persistent CSMA, and CSMA/CD",
                story=story, style_caption=style_caption)
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 6: DETAILED CSMA ALGORITHMIC BREAKDOWN & TRADE-OFFS
    # ==========================================================================
    story.append(Paragraph("5. CSMA Protocol Mechanics — Detailed Algorithmic Breakdown", style_h1))
    story.append(Paragraph(
        "Each CSMA variant embodies a distinct engineering trade-off between channel utilization, collision frequency, "
        "and access delay. Below is the comprehensive algorithmic specification for each implemented strategy:",
        style_body
    ))

    story.append(Paragraph("<b>5.1 Non-Persistent CSMA (Greedy Deferral Strategy):</b>", style_h2))
    story.append(Paragraph(
        "• <b>Algorithm:</b> When a packet arrives, sense the medium. If IDLE (energy = 0.0V), transmit immediately. If BUSY (energy &ge; 1.0V), "
        "immediately abandon carrier sensing and sleep for a random backoff interval <i>T<sub>backoff</sub> = (1 + rand() % 16) &times; Slot</i> before re-sampling.<br/>"
        "• <b>Engineering Trade-off:</b> Prevents synchronous collisions because multiple waiting stations do not retry at the same instant. "
        "However, at light traffic loads, channel efficiency is compromised because the line remains idle while queued stations wait out backoff timers.",
        style_body
    ))

    story.append(Paragraph("<b>5.2 1-Persistent CSMA (Eager Aggressive Strategy):</b>", style_h2))
    story.append(Paragraph(
        "• <b>Algorithm:</b> Sense the medium. If BUSY, keep listening continuously. The instant the line transitions to IDLE, transmit immediately with probability <i>p = 1.0</i>.<br/>"
        "• <b>Engineering Trade-off:</b> Minimizes idle channel delay under light loads. However, under heavy loads, multiple stations accumulate while the channel is busy, "
        "causing a guaranteed synchronous herd collision the moment the line becomes free, collapsing throughput.",
        style_body
    ))

    story.append(Paragraph("<b>5.3 p-Persistent CSMA (Slotted Compromise Strategy):</b>", style_h2))
    story.append(Paragraph(
        "• <b>Algorithm:</b> Channel time is divided into mini-slots of duration &ge; &tau;. When idle, the station transmits with probability <i>p</i>, and defers 1 slot with probability <i>1 - p</i>. "
        "If the slot is deferred and the line remains idle, the station repeats the Bernoulli trial.<br/>"
        "• <b>Engineering Trade-off:</b> Setting optimal persistence factor <i>p* = 1 / N</i> maximizes channel throughput to <i>1/e &asymp; 36.8%</i>. "
        "However, if <i>p</i> is set too low, excessive idle deferrals explode packet latency; if set too high, it degrades into 1-Persistent herd collisions.",
        style_body
    ))

    story.append(Paragraph("<b>5.4 CSMA/CD Protocol Principles (Listen-While-Talk Strategy):</b>", style_h2))
    story.append(Paragraph(
        "• <b>Algorithm:</b> Senses 1-persistently until idle, pauses for a 96-bit Inter-Frame Gap (IFG), then transmits while continuously monitoring total bus voltage. "
        "If voltage doubles (&ge; 2.0V), transmission aborts immediately, emits a 32-bit Jamming signal, and enters Truncated Binary Exponential Backoff (BEB).<br/>"
        "• <b>Engineering Trade-off:</b> Achieves dominant throughput and bounded latency under intense contention by stopping collided transmissions within <i>2 T<sub>p</sub></i>.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 7: IEEE 802.3 CSMA/CD DETAILED FLOWCHART & JAMMING TIMELINE (DIAGRAM 3)
    # ==========================================================================
    story.append(Paragraph("6. IEEE 802.3 CSMA/CD Protocol Engine & Jamming Flowchart", style_h1))
    story.append(Paragraph(
        "CSMA/CD eliminates the massive channel waste inherent in classic CSMA by enabling transmitting stations to detect collisions in real time. "
        "Figure 6.1 details the complete algorithmic flowchart alongside the space-time timeline of collision detection and jamming:",
        style_body
    ))

    # Allot almost full page to the CSMA/CD flowchart & timeline
    embed_chart("diagram_csmacd_detailed_flowchart.png", max_width=485, max_height=500,
                caption="Figure 6.1: (A) Comprehensive IEEE 802.3 CSMA/CD Algorithmic Flowchart; (B) Space-Time Timeline of Collision, Jamming, and Backoff",
                story=story, style_caption=style_caption)
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 8: CSMA/CD OPERATIONAL MECHANICS WALKTHROUGH
    # ==========================================================================
    story.append(Paragraph("7. IEEE 802.3 CSMA/CD Operational Mechanics Walkthrough", style_h1))
    story.append(Paragraph(
        "The IEEE 802.3 CSMA/CD standard defines five interdependent stages that govern channel contention, "
        "instantaneous collision detection, and channel stabilization. Below is the operational walkthrough of each stage:",
        style_body
    ))

    story.append(Paragraph("1. <b>1-Persistent Sensing & Inter-Frame Gap (IFG):</b>", style_h2))
    story.append(Paragraph(
        "A contending station senses the physical wire. If busy, it waits in persistent listening. As soon as the line becomes idle, "
        "the station pauses for the standard 96-bit Inter-Frame Gap (IFG, 9.6 &mu;s at 10 Mbps). This idle gap allows receiver electronics "
        "to recover, drain line capacitance, and prepare for the next frame preamble before transmission begins.",
        style_body
    ))

    story.append(Paragraph("2. <b>Listen-While-Talk Mode (Non-Blocking Concurrency):</b>", style_h2))
    story.append(Paragraph(
        "While actively streaming frame bytes onto the wire, the station continuously samples the shared memory bus using "
        "Listen-While-Talk time slicing (<code>usleep(200)</code>) on <code>bus-&gt;collision_flag</code> and <code>bus-&gt;voltage_level</code>. "
        "If a second station transmits during the vulnerable window, total bus energy doubles to &ge; 2.0V, asserting "
        "<code>bus-&gt;collision_flag = 1</code> and causing transmitting stations to abort immediately.",
        style_body
    ))

    story.append(Paragraph("3. <b>Immediate Transmission Abort:</b>", style_h2))
    story.append(Paragraph(
        "The instant a collision alert is received, the station terminates normal frame transmission. Instead of transmitting doomed bits "
        "for the full frame duration (10.0 ms), transmission is aborted within <i>2 T<sub>p</sub></i> (approx 2.0 ms), saving over 80% of channel airtime.",
        style_body
    ))

    story.append(Paragraph("4. <b>32-Bit Jamming Signal Pattern (0x55555555):</b>", style_h2))
    story.append(Paragraph(
        "Immediately after aborting, the station transmits a 32-bit alternating bit sequence (<code>0x55555555</code>). "
        "This jamming signal reinforces the collision energy across the entire wire, guaranteeing that all other transceivers "
        "reliably detect the collision even if the primary collision wavefront was attenuated.",
        style_body
    ))

    story.append(Paragraph("5. <b>Truncated Binary Exponential Backoff (BEB):</b>", style_h2))
    story.append(Paragraph(
        "The station increments collision counter <i>K &larr; K + 1</i>. It selects a uniform random integer <i>R &isin; [0, 2<sup>min(K, 10)</sup> - 1]</i> "
        "and delays retransmission for <i>T<sub>B</sub> = R &times; 2 T<sub>p</sub></i>. If <i>K &gt; 15</i>, transmission aborts with an Excessive Collisions error.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 9: MATHEMATICAL FORMULATIONS & RENEWAL THEORY DERIVATIONS
    # ==========================================================================
    story.append(Paragraph("8. Mathematical Formulations & Renewal Theory Derivations", style_h1))
    story.append(Paragraph(
        "To rigorously benchmark our empirical results, we apply the classical renewal theory framework formulated by "
        "Leonard Kleinrock and Fouad Tobagi (1975). Let <i>G</i> represent offered traffic load (transmission attempts per frame time) "
        "and let <i>a = T<sub>p</sub> / T<sub>t</sub></i> represent the normalized one-way propagation delay ratio:",
        style_body
    ))

    embed_math_card("formula_non_persistent.png", max_width=485, max_height=60,
                    caption="Formula 8.1: Throughput Equation for Non-Persistent CSMA (Kleinrock & Tobagi, 1975)",
                    story=story, style_caption=style_caption)

    embed_math_card("formula_one_persistent.png", max_width=485, max_height=62,
                    caption="Formula 8.2: Throughput Equation for 1-Persistent CSMA under Renewal Arrival Processes",
                    story=story, style_caption=style_caption)

    embed_math_card("formula_csmacd_efficiency.png", max_width=485, max_height=60,
                    caption="Formula 8.3: IEEE 802.3 CSMA/CD Channel Access Efficiency as a Function of Normalized Delay Ratio a",
                    story=story, style_caption=style_caption)

    embed_math_card("formula_p_optimal.png", max_width=485, max_height=60,
                    caption="Formula 8.4: Derivation of Optimal Persistence Factor p* = 1/N in p-Persistent CSMA",
                    story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Mathematical Analysis & Key Theoretical Insights:</b>", style_h2))
    story.append(Paragraph(
        "• <b>CSMA/CD Efficiency Advantage:</b> In classical CSMA, a collision consumes the entire frame duration <i>T<sub>t</sub> + T<sub>p</sub></i>. "
        "In CSMA/CD, a collision is terminated in <i>2 T<sub>p</sub> + T<sub>jam</sub></i>. Because a contention interval requires an average of "
        "<i>e &asymp; 2.72</i> attempts before success, the wasted contention time is <i>2.72 &times; 2 T<sub>p</sub> = 5.44 T<sub>p</sub></i>, "
        "yielding total cycle time <i>T<sub>t</sub> + 6.44 T<sub>p</sub></i> and efficiency <i>&eta; = 1 / (1 + 6.44 a)</i>.<br/>"
        "• <b>Persistence Trade-off:</b> In p-Persistent CSMA, the probability that exactly one of <i>N</i> contending stations transmits in an idle slot is "
        "<i>P(success) = N p (1 - p)<sup>N - 1</sup></i>. Taking the derivative with respect to <i>p</i> and equating to zero yields <i>p* = 1/N</i>. "
        "At this optimal point, <i>P(success) = (1 - 1/N)<sup>N - 1</sup> &rarr; 1/e &asymp; 36.8%</i> as <i>N &rarr; &infin;</i>.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 10: COLLISION RESOLUTION DYNAMICS & CHANNEL STABILIZATION
    # ==========================================================================
    story.append(Paragraph("9. IEEE 802.3 Collision Resolution Dynamics & Channel Stabilization", style_h1))
    story.append(Paragraph(
        "When repeated collisions occur on the shared bus, the retransmission spacing strategy governs channel stability. "
        "We present the IEEE 802.3 Truncated Binary Exponential Backoff (BEB) formulation and the 32-bit Jamming Signal sequence, "
        "analyzing their roles in contention resolution and medium stabilization:",
        style_body
    ))

    embed_math_card("formula_beb_backoff.png", max_width=485, max_height=75,
                    caption="Formula 9.1: IEEE 802.3 Truncated Binary Exponential Backoff (BEB) Slot Range Formulation",
                    story=story, style_caption=style_caption)

    embed_math_card("formula_jam_sequence.png", max_width=485, max_height=75,
                    caption="Formula 9.2: IEEE 802.3 32-Bit Jamming Signal & Minimum Collision Slot Time Enforcement",
                    story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Collision Resolution Mechanics & Physical Channel Stabilization:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Truncated Exponential Expansion:</b> As collision count <i>k</i> increases, the contention window expands as <i>[0, 2<sup>k</sup> - 1]</i> slots. "
        "For small <i>k</i>, the window remains compact (e.g., <i>2<sup>1</sup> - 1 = 1</i>, <i>2<sup>2</sup> - 1 = 3</i>), minimizing idle slot overhead under light contention. "
        "Under heavy congestion, the window doubles exponentially up to <i>k = 10</i> (1023 slots), diffusing contending stations across time and preventing channel collapse.<br/>"
        "• <b>Truncation Limit (k = 10) & Abort Ceiling (k = 16):</b> At <i>k = 10</i>, window expansion is capped at 1024 slots to prevent latency from growing unboundedly. "
        "If a frame collides 16 consecutive times, the MAC layer aborts transmission and signals an unrecoverable medium failure to higher network layers.<br/>"
        "• <b>The Ethernet Capture Effect:</b> A station that successfully transmits resets its collision counter to <i>k = 0</i>, giving it an immediate contention window of <i>[0, 1]</i>. "
        "In contrast, stations experiencing repeated collisions operate with higher backoff windows (<i>k &ge; 1</i>). Consequently, the newly successful station has a "
        "significantly higher probability of acquiring the channel for subsequent frames, leading to short-term unfairness termed the <i>Ethernet Capture Effect</i>.<br/>"
        "• <b>32-Bit Jamming Pattern Reinforcement:</b> Transceivers at opposite cable boundaries observe attenuated waveforms. Emitting a 32-bit alternating bit pattern "
        "(<code>0x55555555</code>) guarantees that the voltage spike &ge; 2.0V persists across the full round-trip propagation path, ensuring all transceivers abort cleanly.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 11: END-TO-END CODE WORKFLOW & THREAD SYNCHRONIZATION PIPELINE (DIAGRAM 4)
    # ==========================================================================
    story.append(Paragraph("10. End-to-End Multi-Threaded Pipeline & Synchronization Workflow", style_h1))
    story.append(Paragraph(
        "Figure 10.1 details the complete multi-threaded software architecture and execution pipeline implemented in "
        "<code>csma_sim.c</code>. It contrasts the lifecycle of concurrent station worker threads "
        "with the shared broadcast channel coordinator across all 7 pipeline stages:",
        style_body
    ))

    # Allot almost full page to the code workflow diagram
    embed_chart("diagram_code_workflow.png", max_width=485, max_height=500,
                caption="Figure 10.1: End-to-End Multi-Threaded Pipeline Workflow — Station Execution vs. Channel Medium Coordination",
                story=story, style_caption=style_caption)
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 12: END-TO-END ARCHITECTURE WALKTHROUGH & INTUITION
    # ==========================================================================
    story.append(Paragraph("11. End-to-End Architecture Walkthrough & Intuition", style_h1))
    story.append(Paragraph(
        "The project architecture provides maximum execution efficiency and clean synchronization by modeling contending nodes as concurrent "
        "POSIX threads (<code>pthreads</code>) executing over a thread-synchronized broadcast channel medium across three distinct layers:",
        style_body
    ))

    story.append(Paragraph("<b>11.1 Station Worker Thread Pipeline (POSIX pthreads):</b>", style_h2))
    story.append(Paragraph(
        "• <b>Concurrent Worker Threads:</b> Each contending station is spawned via <code>pthread_create()</code>, executing "
        "simultaneously within the shared virtual address space. Stations maintain independent pseudo-random generator seeds "
        "derived from microsecond timestamps and thread station IDs, eliminating correlated backoff sequences.<br/>"
        "• <b>Dedicated MAC State Machines:</b> Each worker thread autonomously executes its MAC protocol loop "
        "(Non-Persistent, 1-Persistent, p-Persistent, or CSMA/CD) throughout its transmission quota without external scheduling dependencies.",
        style_body
    ))

    story.append(Paragraph("<b>11.2 Physical Medium Emulation & Constructive Voltage Superposition:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Shared Broadcast Medium Structure:</b> The physical coaxial medium is represented by the <code>ChannelBus</code> structure, "
        "accessible to all station worker threads and protected by fast POSIX synchronization primitives.<br/>"
        "• <b>Constructive Voltage Superposition:</b> Transmitting stations assert 1.0V each into the shared bus. "
        "Overlapping transmissions superimpose constructively into <i>V<sub>bus</sub> = active_transmitters &times; 1.0V</i>. "
        "When <i>V<sub>bus</sub> &ge; 2.0V</i>, the hardware collision flag is raised immediately.",
        style_body
    ))

    story.append(Paragraph("<b>11.3 POSIX Mutex Synchronization & Listen-While-Talk Preemption:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Fast Mutex & Condition Variables:</b> Thread synchronization is governed by standard <code>pthread_mutex_t</code> "
        "and condition variables (<code>idle_cond</code>, <code>collision_cond</code>), ensuring microsecond-level atomic access.<br/>"
        "• <b>Listen-While-Talk Polling Slices:</b> During transmission in CSMA/CD, the worker thread samples <code>bus->collision_flag</code> "
        "every 100 &mu;s. If detected, the station aborts instantaneously (&lt; 2&tau;), emits the 32-bit Jamming signal "
        "(<code>0x55555555</code>), and triggers Truncated BEB.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 13: STATION MAC ENGINE — CARRIER SENSING & PERSISTENCE (CODE SNIPPET 1)
    # ==========================================================================
    story.append(Paragraph("12. Station MAC Engine: Concurrent Carrier Sensing & State Machine", style_h1))
    story.append(Paragraph(
        "Each station executes as an independent concurrent POSIX thread. To sense channel state, "
        "the station acquires the channel mutex (<code>b-&gt;lock</code>), evaluating wire voltage "
        "and propagation delay before deciding whether to transmit or back off:",
        style_body
    ))

    code_sensing = """/* Concurrent Carrier Sensing & MAC State Machine (csma_sim.c) */
if (strategy == STRATEGY_NON_PERSISTENT) {
    pthread_mutex_lock(&b->lock);
    double now = get_time_ms();
    bool perceived_idle = (b->state == CHAN_IDLE) ||
        (b->active_transmitters > 0 && (now - b->first_tx_start_ms < b->prop_delay_ms));
    pthread_mutex_unlock(&b->lock);

    if (!perceived_idle) {
        args->metrics.busy_senses++;
        double boff = calculate_uniform_delay(b->slot_time_ms, &seed);
        args->metrics.total_backoff_ms += boff;
        sleep_ms(boff);
        continue; /* Retry sensing after uniform random backoff */
    }
} else if (strategy == STRATEGY_1_PERSISTENT || strategy == STRATEGY_CSMA_CD) {
    pthread_mutex_lock(&b->lock);
    while (g_running) {
        double now = get_time_ms();
        bool perceived_idle = (b->state == CHAN_IDLE) ||
            (b->active_transmitters > 0 && (now - b->first_tx_start_ms < b->prop_delay_ms));
        if (perceived_idle) break;
        args->metrics.busy_senses++;
        pthread_cond_wait(&b->idle_cond, &b->lock); /* Greedy wait until idle */
    }
    pthread_mutex_unlock(&b->lock);
} else if (strategy == STRATEGY_P_PERSISTENT) {
    /* Wait for idle, then slotted roll r <= p; defer 1 slot if r > p */
    ...
}"""
    embed_code_box("Concurrent Carrier Sensing & MAC State Machine (csma_sim.c)", code_sensing, story, style_code_compact)
    story.append(Paragraph(
        "<b>Implementation Rationale:</b> Acquiring <code>b-&gt;lock</code> guarantees atomic inspection of channel voltage and "
        "propagation window. Condition variable <code>b-&gt;idle_cond</code> wakes 1-Persistent and CSMA/CD station threads immediately "
        "when the medium transitions from BUSY to IDLE, avoiding CPU-intensive busy-waiting loops across concurrent threads.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 14: CSMA/CD ENGINE — LISTEN-WHILE-TALK, JAMMING & BEB (CODE SNIPPET 2)
    # ==========================================================================
    story.append(Paragraph("13. IEEE 802.3 CSMA/CD Engine: Listen-While-Talk, Jamming & BEB", style_h1))
    story.append(Paragraph(
        "CSMA/CD implements true hardware Listen-While-Talk (LWT) semantics by slicing frame transmission into microsecond "
        "polling intervals. When collision voltage (&ge; 2.0V) is detected, the station thread aborts immediately (&lt; 2&tau;), "
        "broadcasts the 32-bit Jamming signal (<code>0x55555555</code>), and executes Truncated Binary Exponential Backoff (BEB):",
        style_body
    ))

    code_csmacd = """/* Preemptive Listen-While-Talk Polling, 32-Bit Jamming & BEB (csma_sim.c) */
if (strategy == STRATEGY_CSMA_CD) {
    /* Microsecond Listen-While-Talk Polling: 100 us time slices */
    while ((get_time_ms() - t_tx_start) < tx_duration && g_running) {
        pthread_mutex_lock(&b->lock);
        if (b->collision_flag) {
            collided = true;
            pthread_mutex_unlock(&b->lock);
            break; /* Preemptive Abort upon destructive collision spike! */
        }
        pthread_mutex_unlock(&b->lock);
        usleep(100); /* 100 us polling slice */
    }
}

if (collided) {
    args->metrics.collisions++; collision_attempts++;
    if (strategy == STRATEGY_CSMA_CD) {
        /* Emits 32-bit alternating jam pattern (0x55555555) strictly for CSMA/CD */
        pthread_mutex_lock(&b->lock);
        b->total_jams++;
        pthread_mutex_unlock(&b->lock);
        sleep_ms(b->jam_duration_ms);

        /* Truncated BEB: R in [0, 2^min(K, 10) - 1], Slot = 2 * Tau */
        boff = calculate_beb_delay(collision_attempts, b->slot_time_ms, &seed);
        args->metrics.total_backoff_ms += boff;
    } else {
        /* Non-CD schemes: Zero jam signal, uniform random backoff R in [1, 16] */
        boff = calculate_uniform_delay(b->slot_time_ms, &seed);
        args->metrics.total_backoff_ms += boff;
    }
    sleep_ms(boff);
}"""
    embed_code_box("Preemptive Listen-While-Talk, Jamming Signal & Truncated BEB (csma_sim.c)", code_csmacd, story, style_code_compact)
    story.append(Paragraph(
        "<b>Implementation Rationale:</b> Slicing transmission into 100 &mu;s polling steps allows the transmitting thread to detect "
        "destructive voltage spikes (&ge; 2.0V) within <i>2 T<sub>p</sub></i>, saving up to 90% of frame airtime. Emitting the 32-bit "
        "Jamming signal (<code>0x55555555</code>) is strictly restricted to CSMA/CD, ensuring that all contending nodes register "
        "the collision before executing Truncated BEB.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 15: SHARED CHANNEL MEDIUM — VOLTAGE SUPERPOSITION (CODE SNIPPET 3)
    # ==========================================================================
    story.append(Paragraph("14. Shared Channel Medium: Mutex Synchronization & Voltage Superposition", style_h1))
    story.append(Paragraph(
        "The shared coaxial medium resides in the thread-safe <code>ChannelBus</code> structure. It tracks "
        "active station threads concurrently, computes physical line voltage via electromagnetic wave superposition, "
        "and coordinates state transitions between <code>IDLE</code> (0.0V), <code>BUSY</code> (1.0V), and <code>COLLISION</code> (&ge; 2.0V):",
        style_body
    ))

    code_channel = """/* Shared Channel Medium & Voltage Superposition (csma_sim.c) */
ChannelBus bus;
memset(&bus, 0, sizeof(ChannelBus));
pthread_mutex_init(&bus.lock, NULL);
pthread_cond_init(&bus.idle_cond, NULL);
pthread_cond_init(&bus.collision_cond, NULL);

/* Constructive Voltage Superposition upon Transmission Start */
pthread_mutex_lock(&b->lock);
b->total_tx_attempts++;
int my_slot = b->active_transmitters++;
b->active_station_ids[my_slot] = id;

if (b->active_transmitters == 1) {
    b->state = CHAN_BUSY;
    b->voltage = 1.0f;
    b->collision_flag = false;
    b->first_tx_start_ms = get_time_ms();
} else {
    /* Voltage Superposition: V_bus = active_transmitters * 1.0V (>= 2.0V Collision!) */
    b->state = CHAN_COLLISION;
    b->voltage = (float)b->active_transmitters;
    b->collision_flag = true;
    b->total_collisions++;
    pthread_cond_broadcast(&b->collision_cond);
}
pthread_mutex_unlock(&b->lock);"""
    embed_code_box("Shared Channel Allocation & Voltage Superposition (csma_sim.c)", code_channel, story, style_code_compact)
    story.append(Paragraph(
        "<b>Implementation Rationale:</b> A direct in-memory <code>ChannelBus</code> structure provides microsecond access latency with zero "
        "network stack or IPC overhead. POSIX mutex and condition variables allow concurrent station threads "
        "to synchronize reliably with sub-millisecond precision, completely eliminating race conditions and deadlocks.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 16: MULTI-THREADED LIFECYCLE & THREAD JOINING (CODE SNIPPET 4)
    # ==========================================================================
    story.append(Paragraph("15. Multi-Threaded Coordinator Lifecycle & Menu-Driven Architecture", style_h1))
    story.append(Paragraph(
        "The simulation is 100% interactive and menu-driven without command-line argument dependencies. The coordinator manages the complete lifecycle "
        "of contending station threads: initializing the shared channel medium, spawning concurrent worker threads via <code>pthread_create()</code>, "
        "joining their completion via <code>pthread_join()</code>, and aggregating per-station performance metrics:",
        style_body
    ))

    code_framing = """/* Coordinator: pthread_create(), pthread_join(), and Metrics Logging (csma_sim.c) */
pthread_t threads[MAX_STATIONS];
StationThreadArgs args[MAX_STATIONS];
double sim_start = get_time_ms();

/* Spawn N concurrent station threads simultaneously */
for (int i = 0; i < num_stations; i++) {
    args[i].station_id = i + 1;
    args[i].strategy = strategy;
    args[i].num_frames = num_frames;
    args[i].p_val = p_val;
    args[i].bus = &bus;
    pthread_create(&threads[i], NULL, station_worker_thread, &args[i]);
}

/* Wait for all station threads to complete (pthread_join) */
for (int i = 0; i < num_stations; i++) {
    pthread_join(threads[i], NULL);
}

/* Compute Delivery Success Ratio & Aggregate Global Throughput */
double delivery_rate = ((double)bus.total_successful_frames /
                        (double)(num_stations * num_frames)) * 100.0;
double useful_tx_ms  = bus.total_successful_frames * bus.frame_tx_time_ms;
double efficiency    = useful_tx_ms / (sim_duration * 1000.0);

/* Export live empirical benchmark to results/data/live_c_benchmarks.csv */
FILE *fp_csv = fopen("results/data/live_c_benchmarks.csv", "a");
if (fp_csv) {
    fprintf(fp_csv, "%s,%d,%d,%u,%u,%u,%u,%.4f,%.2f\\n",
            strategy_to_slug(strategy), num_stations, num_frames,
            bus.total_tx_attempts, bus.total_successful_frames,
            bus.total_collisions, bus.total_jams, efficiency, sim_duration);
    fclose(fp_csv);
}"""
    embed_code_box("Multi-Threaded Lifecycle Management & Thread Joining (csma_sim.c)", code_framing, story, style_code_compact)
    story.append(Paragraph(
        "<b>Implementation Rationale:</b> Modeling stations as concurrent POSIX threads provides true multi-core parallel execution "
        "with zero memory copy or process initialization overhead. Joining threads via <code>pthread_join()</code> guarantees clean "
        "synchronization and reliable metric aggregation before reporting global throughput and efficiency.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 17: EXPERIMENT 1 — REQUIREMENT (i) p-PERSISTENT CSMA OPTIMIZATION
    # ==========================================================================
    story.append(Paragraph("16. Experiment 1: Requirement (i) — p-Persistent CSMA Optimization", style_h1))
    story.append(Paragraph(
        "<b>Requirement (i) Specification:</b> Emulate p-Persistent CSMA and evaluate throughput as a function "
        "of persistence probability <i>p &isin; [0.02, 1.00]</i> across contending station threads <i>N &isin; {3, 5, 10}</i> "
        "transmitting 500 frames per station (totaling 1,500 to 5,000 transmitted frames per sweep configuration):",
        style_body
    ))

    embed_chart("1_p_persistent_throughput_vs_p.png", max_width=485, max_height=265,
                caption="Figure 16.1: Channel Throughput S vs. Persistence Factor p across N in {3, 5, 10} Contending Stations (500 Frames/Station)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Theoretical Prediction:</b> Formula 8.4 mathematically derives that the channel acquisition success probability "
        "<i>P(success) = N p (1 - p)<sup>N - 1</sup></i> is strictly maximized at <i>p* = 1/N</i>. For <i>N = 3</i>, <i>p* = 0.33</i>; "
        "for <i>N = 5</i>, <i>p* = 0.20</i>; and for <i>N = 10</i>, <i>p* = 0.10</i>.<br/>"
        "• <b>Empirical Results & Live C Simulator Alignment:</b> In the live multi-threaded C simulator (<code>csma_sim.c</code>), "
        "stations measure empirical channel acquisition efficiency: for <i>N = 10</i> stations with 50 frames/station (500 delivered frames), "
        "the simulator yields <b>39.20%</b> efficiency (25.09 kbps), matching theoretical <i>P(success) = 10 &times; 0.10 &times; (0.90)<sup>9</sup> = 38.74%</i> within 0.46%. "
        "In the slotted contention sweep (Figure 16.1, 500 frames/stn with mini-slot ratio <i>a = 0.10</i>), contention resolves in microsecond mini-slots "
        "so throughput normalizes to <i>S = P<sub>s</sub> / (P<sub>s</sub> + a(1 - P<sub>s</sub>))</i>, peaking at <b>88.6%</b> for <i>N = 3</i> (at p=0.33), "
        "<b>87.4%</b> for <i>N = 5</i> (at p=0.20), and <b>87.0%</b> for <i>N = 10</i> (at p=0.10).<br/>"
        "• <b>What Happened to Throughput as p &rarr; 1.0?</b> For all <i>N</i>, channel throughput exhibits a steep collapse as <i>p &rarr; 1.0</i>, "
        "crashing to <b>0.0%</b>. <i>Why?</i> At <i>p = 1.0</i>, every contending station transmits in every slot with certainty. "
        "With <i>N &ge; 2</i> stations, collisions occur on 100% of attempts, annihilating useful payload throughput.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 18: EXPERIMENT 1 CONTINUED — CONTENTION PENALTIES & LATENCY U-CURVE
    # ==========================================================================
    story.append(Paragraph("17. Experiment 1 Continued: Contention Penalties & Latency U-Curve", style_h1))
    story.append(Paragraph(
        "Evaluating collision frequency and packet delivery latency across persistence probability <i>p &isin; [0.02, 1.00]</i> "
        "reveals the operational penalties when <i>p</i> deviates from optimal <i>p* = 1/N</i> "
        "(evaluated across <i>N &isin; {3, 5, 10}</i> stations with 500 frames per station):",
        style_body
    ))

    embed_chart("2_p_persistent_collisions_and_delay.png", max_width=485, max_height=260,
                caption="Figure 17.1: Contention Penalties in p-Persistent CSMA: (A) Total Collisions vs. p; (B) Average Packet Latency vs. p (N in {3, 5, 10} Stations, 500 Frames/Station)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>What Happened to Collisions (Figure 17.1A)?</b> Total collision count monotonically increases with persistence <i>p</i>. "
        "For <i>N = 10</i> (500 frames/station), collisions escalate by four orders of magnitude from 100 at <i>p = 0.02</i> to 893 at optimal <i>p = 0.10</i>, "
        "exceeding 1,000,000 as <i>p &rarr; 1.0</i>. <i>Why?</i> Multi-station collision probability <i>P(collision) = 1 - (1-p)<sup>N</sup> - N p (1-p)<sup>N-1</sup></i> accelerates aggressively with <i>p</i>.<br/>"
        "• <b>The Latency Convex U-Curve (Figure 17.1B):</b> Packet delivery latency exhibits a distinct convex U-curve across the probability spectrum, with global minimums marked by stars. "
        "At low <i>p &le; 0.05</i>, latency is elevated (25.59 slots for <i>N=3</i>; 19.82 slots for <i>N=5</i>) because stations defer excessively over idle slots due to low transmission odds (<i>1 - p</i>). "
        "At high <i>p &ge; 0.50</i>, latency explodes exponentially (&gt; 113 slots for <i>N=10</i>; &gt; 160 slots for <i>N=5</i> at <i>p=0.80</i>) due to repeated collision retries. "
        "The minimum latency coincides exactly at <b><i>p* = 1/N</i></b> (11.29 slots for <i>N=3</i>; 11.44 slots for <i>N=5</i>; 11.49 slots for <i>N=10</i>), proving that optimal persistence minimizes mean packet delay.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 19: EXPERIMENT 2 — REQUIREMENT (ii) CONTENTION SCALING (N = 1 to 35)
    # ==========================================================================
    story.append(Paragraph("18. Experiment 2: Requirement (ii) — Saturated Contention Scaling", style_h1))
    story.append(Paragraph(
        "<b>Requirement (ii) Specification:</b> Emulate multiple contending stations under each of the 4 CSMA strategies, "
        "systematically sweeping the number of contending stations <i>N</i> from 1 to 35 under saturated queue conditions "
        "with 400 frames transmitted per station (totaling 400 to 14,000 frames per parametric benchmark):",
        style_body
    ))

    embed_chart("3_stations_vs_throughput.png", max_width=485, max_height=265,
                caption="Figure 18.1: Saturated Network Throughput S vs. Contending Network Stations N = 1 to 35 (400 Frames/Station Saturated Load)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>The 1-Persistent Throughput Collapse:</b> At <i>N = 1</i>, 1-Persistent achieves 91.2% throughput. However, as <i>N</i> scales to 35 "
        "(400 frames/stn), throughput crashes catastrophically to <b>0.0% (total herd deadlock)</b>, dropping to 17.5% at N=5 and 1.3% at N=10. "
        "<i>Why?</i> With greedy sensing and probability 1.0, all queued stations transmit simultaneously the instant the line clears, "
        "causing 231,610 collisions and completely locking the medium.<br/>"
        "• <b>CSMA/CD Contention Resilience:</b> CSMA/CD maintains <b>80.6% at N = 5, 64.7% at N = 10, and 55.1% at N = 35</b> "
        "(nearly infinite advantage over collapsed 1-Persistent). <i>Why?</i> Listen-While-Talk detects voltage &ge; 2.0V within <i>2 T<sub>p</sub></i> "
        "and aborts early, while Truncated BEB spreads retries across up to 1024 slots.<br/>"
        "• <b>Non-Persistent & p-Persistent Scaling:</b> Non-Persistent achieves 65.1% at N=5, 50.8% at N=10, and 8.4% at N=35. "
        "p-Persistent (tuned with <i>p = 1/N</i>) sustains <b>51.2% at N=5, 50.4% at N=10, and 50.5% at N=35</b> across all scales.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 20: EXPERIMENT 2 CONTINUED — COLLISION SCALING & ABORT SAVINGS
    # ==========================================================================
    story.append(Paragraph("19. Experiment 2 Continued: Collision Rate Escalation & Abort Savings", style_h1))
    story.append(Paragraph(
        "To evaluate how collision dynamics degrade the channel under intense contention, we measure total collisions "
        "and empirical collision probability across <i>N &isin; [1, 35]</i> contending stations transmitting 400 frames per station:",
        style_body
    ))

    embed_chart("4_stations_vs_collisions.png", max_width=485, max_height=260,
                caption="Figure 19.1: Collision Scaling Under Multi-Station Contention: (A) Total Collisions vs. N; (B) Empirical Collision Rate (%) vs. N (N = 1 to 35 Stations, 400 Frames/Station)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Collision Rate Escalation (Figure 19.1B):</b> In 1-Persistent CSMA (400 frames/stn), the collision rate escalates to "
        "<b>92.4% at N = 5 and 100.0% at N = 35</b>, generating 231,610 collisions. In Non-Persistent CSMA, collisions reach 11,715 (97.5% rate) at N = 35. "
        "In p-Persistent CSMA with <i>p = 1/N</i>, collisions are capped at only 428 (58.8% rate) at N = 35.<br/>"
        "• <b>Why Collision Abortion Saves the Channel in CSMA/CD:</b> Although CSMA/CD logs 1,252 collisions at N = 35, each collision is aborted in "
        "<i>2 T<sub>p</sub> + T<sub>jam</sub></i> (approx 2.5 ms) rather than transmitting the full 64-byte frame (8.0 ms). Over 1,252 collisions, "
        "CSMA/CD saves over <b>6.88 seconds of wasted wire airtime</b>, allowing genuine payload data to achieve 55.1% channel efficiency.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 21: EXPERIMENT 2 CONTINUED — LATENCY INFLATION
    # ==========================================================================
    story.append(Paragraph("20. Experiment 2 Continued: Latency & Channel Access Delay", style_h1))
    story.append(Paragraph(
        "Packet delivery latency measures the average time elapsed from when a frame arrives at the MAC layer until it is "
        "successfully received across the shared medium, benchmarking Quality of Service across <i>N = 1</i> to 35 stations with 400 frames per station:",
        style_body
    ))

    embed_chart("5_stations_vs_delay.png", max_width=485, max_height=265,
                caption="Figure 20.1: Average Packet Transmission Latency (Time Slots) vs. Contending Network Stations N (N = 1 to 35 Stations, 400 Frames/Station)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Catastrophic Latency Explosion in 1-Persistent CSMA:</b> At <i>N = 1</i>, packet delay is 19.8 slots. As <i>N</i> scales to 10 (400 frames/stn), "
        "1-Persistent delay explodes to <b>7,533.9 slots</b>, and beyond N=20 stations enter total collision deadlock. "
        "<i>Why?</i> Every collision forces stations into backoff; upon waking, persistent sensing triggers immediate re-collision.<br/>"
        "• <b>CSMA/CD Latency Containment:</b> CSMA/CD bounds average delay to <b>21.9 slots at N=5, 66.7 slots at N=10, and 235.1 slots at N=35</b> "
        "(a <b>93.5% latency reduction</b> relative to Non-Persistent's 3,637.4 slots and p-Persistent's 594.9 slots). "
        "<i>Why?</i> Truncating damaged frames in <i>2 T<sub>p</sub></i> clears contention stages rapidly, preventing queue backlog buildup.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 22: EXPERIMENT 2 CONTINUED — PROTOCOL EFFICIENCY COMPARISON
    # ==========================================================================
    story.append(Paragraph("21. Experiment 2 Continued: Channel Access Efficiency Ranking", style_h1))
    story.append(Paragraph(
        "Channel access efficiency &eta; measures the proportion of total channel operating time dedicated to successful, "
        "unimpaired payload delivery: <i>&eta; = T<sub>useful</sub> / T<sub>total</sub></i> across <i>N = 1</i> to 35 stations with 400 frames per station:",
        style_body
    ))

    embed_chart("6_stations_vs_channel_efficiency.png", max_width=485, max_height=145,
                caption="Figure 21.1: Normalized Channel Access Efficiency eta (%) vs. Contending Stations N (N = 1 to 35 Stations, 400 Frames/Station)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>In-Depth Comparative Analysis: Why the Four Strategies Rank Where They Do:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Rank 1 — CSMA/CD (IEEE 802.3): 55.1% Efficiency at N = 35 (400 Frames/Station)</b><br/>"
        "  <i>Dominance Factors:</i> (1) <b>Listen-While-Talk Abortion:</b> Colliding transceivers detect voltage &ge; 2.0V within round-trip time <i>2 T<sub>p</sub></i> (&asymp; 2.0 ms), emit a 32-bit jam signal, and abort immediately, capping collision waste to only <i>2 T<sub>p</sub> + T<sub>jam</sub> &asymp; 2.5 ms</i> (saving 68% wasted airtime vs 8.0 ms full frame). (2) <b>Truncated BEB:</b> Contention windows double up to 1024 slots (<i>2<sup>min(k, 10)</sup></i>), desynchronizing competing stations across time.<br/>"
        "• <b>Rank 2 — p-Persistent CSMA (p = 1/N): 50.5% Efficiency at N = 35 (400 Frames/Station)</b><br/>"
        "  <i>Second-Place Factors:</i> By testing probability <i>p* = 1/N</i> on idle slots, contending stations scatter attempts geometrically across successive mini-slots. If a station defers, it waits 1 slot and re-evaluates. This pacing keeps collisions capped at 428 without CD hardware. However, lacking collision abort, colliding frames waste full 8.0 ms durations, keeping it below CSMA/CD.<br/>"
        "• <b>Rank 3 — Non-Persistent CSMA: 8.4% Efficiency at N = 35 (400 Frames/Station)</b><br/>"
        "  <i>Degradation Factors:</i> Defers uniformly (1 to 16 slots) when sensing busy. While effective at light loads (65.1% at N=5), under 35 saturated stations, nodes accumulate in backoff queues and wake up in synchronized waves. Finding the line momentarily idle, multiple nodes transmit blind 64-byte frames simultaneously, driving collisions to 11,715 (97.5% rate) and latency to 3,637 slots.<br/>"
        "• <b>Rank 4 — 1-Persistent CSMA: 0.0% Efficiency at N = 35 (Total Herd Deadlock)</b><br/>"
        "  <i>Collapse Factors:</i> Persistently waits while busy and transmits with certainty (<i>p = 1.0</i>) immediately upon line release. With multiple stations queued during any frame, ALL queued nodes transmit simultaneously the instant the line clears, causing a 100% collision cascade (231,610 collisions) and completely locking the medium into zero throughput.",
        style_explain
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 23: EXPERIMENT 3 — CSMA/CD EFFICIENCY vs PROPAGATION DELAY RATIO a
    # ==========================================================================
    story.append(Paragraph("22. Experiment 3: CSMA/CD Efficiency vs Propagation Delay Ratio a", style_h1))
    story.append(Paragraph(
        "We investigated the fundamental physical relationship between CSMA/CD efficiency &eta; and the normalized "
        "one-way propagation delay ratio <i>a = T<sub>p</sub> / T<sub>t</sub></i> across multi-station contention "
        "(evaluated under <i>N = 10</i> contending stations transmitting 500 frames per station, totaling 5,000 frames per sweep configuration):",
        style_body
    ))

    embed_chart("8_csmacd_efficiency_vs_propagation_delay_a.png", max_width=485, max_height=265,
                caption="Figure 22.1: CSMA/CD Channel Efficiency eta vs. Normalized Delay Ratio a = Tp / Tt (N = 10 Stations, 500 Frames/Station Saturated Load)",
                story=story, style_caption=style_caption)

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>The 'Speed Limit' of CSMA/CD:</b> As the propagation delay ratio <i>a = T<sub>p</sub> / T<sub>t</sub></i> increases from 0.001 to 0.5, "
        "CSMA/CD efficiency plummets from <b>99.4% down to 23.7%</b>. <i>Why?</i> As link bandwidth scales from 10 Mbps to 100 Mbps (Fast Ethernet) "
        "and 1 Gbps (Gigabit Ethernet), frame transmission time <i>T<sub>t</sub></i> shrinks by orders of magnitude while physical light speed in copper "
        "(200,000 km/s) remains constant! Consequently, <i>a = T<sub>p</sub> / T<sub>t</sub></i> grows rapidly, turning contention intervals into the dominant fraction of channel time.<br/>"
        "• <b>Why Gigabit Ethernet Abandoned Shared CSMA/CD:</b> To maintain CSMA/CD at 1 Gbps across a 200m network diameter, Ethernet would "
        "require a minimum frame size of 5120 bits (640 bytes) or carrier extension, severely wasting capacity for small packets. "
        "This physical limitation drove the industry to abandon shared bus CSMA/CD and adopt full-duplex switched Ethernet.",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 24: EXPERIMENT 4 — LIVE MULTI-THREADED POSIX BENCHMARK VALIDATION
    # ==========================================================================
    story.append(Paragraph("23. Experiment 4: Live Multi-Threaded POSIX Benchmark Validation", style_h1))
    story.append(Paragraph(
        "To validate our multi-threaded C implementation under live Linux operating system concurrency, we executed "
        "concurrent test runs of <code>bin/csma_sim</code> with independent station threads spawned via <code>pthread_create()</code> "
        "contending over the shared channel bus with POSIX mutex and condition variable synchronization:",
        style_body
    ))

    live_table_data = [
        [Paragraph("<b>MAC Strategy</b>", style_table_header),
         Paragraph("<b>Stations (N)</b>", style_table_header),
         Paragraph("<b>Frames/Stn</b>", style_table_header),
         Paragraph("<b>Delivered</b>", style_table_header),
         Paragraph("<b>Collisions</b>", style_table_header),
         Paragraph("<b>Throughput (kbps)</b>", style_table_header),
         Paragraph("<b>Efficiency (%)</b>", style_table_header),
         Paragraph("<b>Wall Time (s)</b>", style_table_header)],
        [Paragraph("<b>CSMA/CD (802.3)</b>", style_table), Paragraph("10", style_table), Paragraph("5", style_table), Paragraph("50", style_table), Paragraph("54", style_table), Paragraph("<b>29.33</b>", style_table_bold), Paragraph("<b>45.82%</b>", style_table_bold), Paragraph("<b>0.87s</b>", style_table_bold)],
        [Paragraph("Non-Persistent", style_table), Paragraph("10", style_table), Paragraph("5", style_table), Paragraph("50", style_table), Paragraph("53", style_table), Paragraph("22.52", style_table), Paragraph("35.18%", style_table), Paragraph("1.14s", style_table)],
        [Paragraph("1-Persistent", style_table), Paragraph("10", style_table), Paragraph("5", style_table), Paragraph("47", style_table), Paragraph("143", style_table), Paragraph("19.47", style_table), Paragraph("30.43%", style_table), Paragraph("1.24s", style_table)],
        [Paragraph("p-Persistent (p=0.10)", style_table), Paragraph("10", style_table), Paragraph("5", style_table), Paragraph("50", style_table), Paragraph("1", style_table), Paragraph("17.29", style_table), Paragraph("27.01%", style_table), Paragraph("1.48s", style_table)],
        [Paragraph("p-Persistent (p=0.10)", style_table), Paragraph("10", style_table), Paragraph("50", style_table), Paragraph("500", style_table), Paragraph("23", style_table), Paragraph("25.09", style_table), Paragraph("39.20%", style_table), Paragraph("10.20s", style_table)],
        [Paragraph("p-Persistent (p=0.33)", style_table), Paragraph("3", style_table), Paragraph("10", style_table), Paragraph("30", style_table), Paragraph("0", style_table), Paragraph("33.62", style_table), Paragraph("52.52%", style_table), Paragraph("0.46s", style_table)],
        [Paragraph("CSMA/CD (802.3)", style_table), Paragraph("4", style_table), Paragraph("15", style_table), Paragraph("60", style_table), Paragraph("19", style_table), Paragraph("37.00", style_table), Paragraph("57.81%", style_table), Paragraph("0.88s", style_table)],
        [Paragraph("CSMA/CD (802.3)", style_table), Paragraph("2", style_table), Paragraph("15", style_table), Paragraph("30", style_table), Paragraph("2", style_table), Paragraph("62.11", style_table), Paragraph("97.04%", style_table), Paragraph("0.26s", style_table)],
    ]
    t_live = Table(live_table_data, colWidths=[105, 45, 50, 50, 48, 70, 60, 57])
    t_live.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B4F72')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_live)
    story.append(Paragraph("<i>Table 23.1: Live Linux Multi-Threaded Empirical Benchmark Metrics (Evaluated across N in {2, 3, 4, 10} Stations and 5 to 50 Frames/Station)</i>", style_caption))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Theoretical vs. Empirical In-Depth 'What & Why' Analysis:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Throughput & Efficiency Dominance of CSMA/CD:</b> Under identical contention (<i>N = 10</i> stations, 5 frames/stn, 50 delivered frames), "
        "CSMA/CD delivers the highest efficiency (<b>45.82%</b>, 29.33 kbps) and fastest execution time (<b>0.87s</b>), outperforming Non-Persistent (35.18%, 1.14s), "
        "1-Persistent (30.43%, 1.24s), and p-Persistent with p=0.10 (27.01%, 1.48s). <i>Why?</i> Slicing transmission into 100 &mu;s polling slices allows CSMA/CD "
        "to detect collisions within <i>2 T<sub>p</sub></i> (&approx; 2.0 ms), emit a 32-bit jam signal, and abort doomed transmissions 4&times; faster than non-CD strategies.<br/>"
        "• <b>Contention Dispersal & High-Load Convergence:</b> When the workload is scaled to <i>N = 10</i> stations with 50 frames/stn (500 delivered frames), "
        "p-Persistent (p=0.10) throughput climbs from 17.29 kbps to <b>25.09 kbps (39.20% efficiency)</b>, matching the theoretical optimal prediction "
        "<i>P<sub>succ</sub> = 10 &times; 0.10 &times; (0.90)<sup>9</sup> = 38.74%</i> within 0.46%. At light load (<i>N = 2</i>, 15 frames/stn), CSMA/CD reaches <b>97.04% line efficiency</b> (62.11 kbps).",
        style_body
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 25: MASTER PERFORMANCE COMPARISON MATRIX ACROSS ALL METRICS
    # ==========================================================================
    story.append(Paragraph("24. Master Contention Scaling & Performance Comparison", style_h1))
    story.append(Paragraph(
        "Table 24.1 synthesizes our comprehensive findings across throughput, collision scaling, latency inflation, "
        "and efficiency degradation across all four implemented MAC strategies over high station counts (<i>N = 1</i> to $35$ with 400 frames/station):",
        style_body
    ))

    master_summary_data = [
        [Paragraph("<b>MAC Strategy</b>", style_table_header),
         Paragraph("<b>Stations (N)</b>", style_table_header),
         Paragraph("<b>Frames/Stn</b>", style_table_header),
         Paragraph("<b>Throughput (S)</b>", style_table_header),
         Paragraph("<b>Collisions</b>", style_table_header),
         Paragraph("<b>Collision Rate</b>", style_table_header),
         Paragraph("<b>Delay (slots)</b>", style_table_header),
         Paragraph("<b>Efficiency (&eta;)</b>", style_table_header)],
        [Paragraph("<b>CSMA/CD (802.3)</b>", style_table), Paragraph("5", style_table), Paragraph("400", style_table), Paragraph("0.8060", style_table), Paragraph("173", style_table), Paragraph("36.6%", style_table), Paragraph("21.94", style_table), Paragraph("80.6%", style_table)],
        [Paragraph("<b>CSMA/CD (802.3)</b>", style_table), Paragraph("20", style_table), Paragraph("400", style_table), Paragraph("0.5728", style_table), Paragraph("941", style_table), Paragraph("75.8%", style_table), Paragraph("142.56", style_table), Paragraph("57.3%", style_table)],
        [Paragraph("<b>CSMA/CD (802.3)</b>", style_table), Paragraph("35", style_table), Paragraph("400", style_table), Paragraph("<b>0.5514</b>", style_table_bold), Paragraph("1252", style_table), Paragraph("80.7%", style_table), Paragraph("<b>235.09</b>", style_table_bold), Paragraph("<b>55.1%</b>", style_table_bold)],
        [Paragraph("p-Persistent (p=1/N)", style_table), Paragraph("5", style_table), Paragraph("400", style_table), Paragraph("0.5119", style_table), Paragraph("377", style_table), Paragraph("55.7%", style_table), Paragraph("101.20", style_table), Paragraph("51.2%", style_table)],
        [Paragraph("p-Persistent (p=1/N)", style_table), Paragraph("20", style_table), Paragraph("400", style_table), Paragraph("0.4910", style_table), Paragraph("457", style_table), Paragraph("60.4%", style_table), Paragraph("370.99", style_table), Paragraph("49.1%", style_table)],
        [Paragraph("p-Persistent (p=1/N)", style_table), Paragraph("35", style_table), Paragraph("400", style_table), Paragraph("0.5051", style_table), Paragraph("428", style_table), Paragraph("58.8%", style_table), Paragraph("594.85", style_table), Paragraph("50.5%", style_table)],
        [Paragraph("Non-Persistent", style_table), Paragraph("5", style_table), Paragraph("400", style_table), Paragraph("0.6509", style_table), Paragraph("173", style_table), Paragraph("36.6%", style_table), Paragraph("78.51", style_table), Paragraph("65.1%", style_table)],
        [Paragraph("Non-Persistent", style_table), Paragraph("20", style_table), Paragraph("400", style_table), Paragraph("0.2731", style_table), Paragraph("1933", style_table), Paragraph("86.6%", style_table), Paragraph("672.53", style_table), Paragraph("27.3%", style_table)],
        [Paragraph("Non-Persistent", style_table), Paragraph("35", style_table), Paragraph("400", style_table), Paragraph("0.0836", style_table), Paragraph("11715", style_table), Paragraph("97.5%", style_table), Paragraph("3637.39", style_table), Paragraph("8.4%", style_table)],
        [Paragraph("1-Persistent", style_table), Paragraph("5", style_table), Paragraph("400", style_table), Paragraph("0.1747", style_table), Paragraph("3657", style_table), Paragraph("92.4%", style_table), Paragraph("287.29", style_table), Paragraph("17.5%", style_table)],
        [Paragraph("1-Persistent", style_table), Paragraph("20", style_table), Paragraph("400", style_table), Paragraph("0.0001", style_table), Paragraph("132282", style_table), Paragraph("100.0%", style_table), Paragraph("13915.50", style_table), Paragraph("0.0%", style_table)],
        [Paragraph("1-Persistent", style_table), Paragraph("35", style_table), Paragraph("400", style_table), Paragraph("0.0000", style_table), Paragraph("231610", style_table), Paragraph("100.0%", style_table), Paragraph("Deadlock", style_table), Paragraph("0.0%", style_table)],
    ]
    t_summary = Table(master_summary_data, colWidths=[105, 45, 50, 55, 50, 60, 60, 60])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B4F72')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_summary)
    story.append(Paragraph("<i>Table 24.1: Master MAC Contention Benchmark Synthesis Across 1 to 35 Contending Stations (400 Frames/Station Saturated Load)</i>", style_caption))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Cross-Strategy Comparative Synthesis: Why Protocols Settle into Their Respective Tiers:</b>", style_h2))
    story.append(Paragraph(
        "• <b>Collision Waste Asymmetry (CSMA/CD vs. Non-CD Schemes):</b> The fundamental dividing line between CSMA/CD and the three non-CD strategies is the <i>airtime penalty per collision</i>. In 1-Persistent, Non-Persistent, and p-Persistent, colliding stations transmit blind for the full 64-byte frame (<i>T<sub>t</sub> = 8.0 ms</i>). In CSMA/CD, transceivers listen while transmitting and abort as soon as voltage &ge; 2.0V is observed within <i>2 T<sub>p</sub> + T<sub>jam</sub> &asymp; 2.5 ms</i>. Across 1,252 collisions at N = 35, CSMA/CD saves over <b>6.88 seconds of wasted airtime</b>, allowing genuine data payload to capture 55.1% channel capacity.<br/>"
        "• <b>Contention Window Adaptation (Dynamic BEB vs. Static 1–16 Slots):</b> When station density expands to N = 35, CSMA/CD's Truncated BEB dynamically scales its backoff window from 2 up to 1024 slots (<i>2<sup>min(k, 10)</sup></i>), dispersing retransmissions and avoiding repeated clashes. In contrast, Non-Persistent and 1-Persistent employ static 1–16 slot random backoff; a 16-slot window is overwhelmed by 35 competing stations, causing re-colliding stations to repeatedly pick identical slots.<br/>"
        "• <b>Access Aggressiveness Spectrum (Greedy 1-Persistent vs. Tuned p-Persistent):</b> 1-Persistent is overly aggressive: stations wait while busy and fire with certainty (<i>p = 1.0</i>) immediately upon line clearance, guaranteeing herd deadlock (0.0% throughput, 231,610 collisions). p-Persistent tempers this aggressiveness by tuning transmission probability to <i>p = 1/N</i>, achieving a near-optimal success probability <i>(1 - 1/N)<sup>N - 1</sup> &rarr; 1/e &asymp; 36.8%</i>. This mathematical throttling enables p-Persistent to achieve near-CD efficiency (50.5%) even without collision abort hardware.<br/>"
        "• <b>Delay Trade-offs & Queue Backlog:</b> Non-Persistent's excessive deferrals at low loads and blind collision cascades at high loads drive latency to 3,637.4 slots. CSMA/CD's immediate 2.0 ms collision truncation clears doomed transmission attempts rapidly, bounding average packet delay to 235.1 slots (saving over 93.5% latency).",
        style_explain
    ))
    story.append(PageBreak())

    # ==========================================================================
    # PAGE 26: GRAND PROTOCOL COMPARISON MATRIX & QUANTITATIVE SYNTHESIS
    # ==========================================================================
    story.append(Paragraph("25. Grand Protocol Comparison Matrix & Quantitative Synthesis", style_h1))
    story.append(Paragraph(
        "Table 25.1 provides a comprehensive comparative synthesis of all four evaluated CSMA protocols, "
        "summarizing their carrier sensing mechanisms, collision detection capabilities, vulnerability periods, backoff algorithms, and empirical performance metrics:",
        style_body
    ))

    # Refined 5-column table without ALOHA, with generous column widths for crystal-clear readability
    matrix_data = [
        [Paragraph("<b>Metric / Parameter</b>", style_table_header),
         Paragraph("<b>Non-Persistent CSMA</b>", style_table_header),
         Paragraph("<b>1-Persistent CSMA</b>", style_table_header),
         Paragraph("<b>p-Persistent CSMA</b>", style_table_header),
         Paragraph("<b>CSMA/CD (IEEE 802.3)</b>", style_table_header)],

        [Paragraph("<b>Carrier Sensing</b>", style_table),
         Paragraph("Senses; random backoff if busy", style_table),
         Paragraph("Senses; waits persistently", style_table),
         Paragraph("Senses; waits until idle", style_table),
         Paragraph("Senses; 1-persistent sensing", style_table)],

        [Paragraph("<b>Collision Detection</b>", style_table),
         Paragraph("No (blind transmission)", style_table),
         Paragraph("No (blind transmission)", style_table),
         Paragraph("No (blind transmission)", style_table),
         Paragraph("<b>Yes (Listen-While-Talk)</b>", style_table_bold)],

        [Paragraph("<b>Vulnerable Window</b>", style_table),
         Paragraph("&tau; = T<sub>p</sub>", style_table),
         Paragraph("&tau; = T<sub>p</sub>", style_table),
         Paragraph("&tau; = T<sub>p</sub>", style_table),
         Paragraph("<b>2 &tau; = 2 T<sub>p</sub></b> (RTT)", style_table_bold)],

        [Paragraph("<b>Collision Abortion</b>", style_table),
         Paragraph("No (wastes full frame T<sub>t</sub>)", style_table),
         Paragraph("No (wastes full frame T<sub>t</sub>)", style_table),
         Paragraph("No (wastes full frame T<sub>t</sub>)", style_table),
         Paragraph("<b>Yes (Instant abort + Jam)</b>", style_table_bold)],

        [Paragraph("<b>Backoff Algorithm</b>", style_table),
         Paragraph("Random backoff window", style_table),
         Paragraph("Random / persistent deferral", style_table),
         Paragraph("Geometric slot deference", style_table),
         Paragraph("<b>Truncated BEB (2<sup>min(K,10)</sup>)</b>", style_table_bold)],

        [Paragraph("<b>Peak Throughput S</b>", style_table),
         Paragraph("~ 81.5% (at a=0.01)", style_table),
         Paragraph("~ 53.0% (at a=0.01)", style_table),
         Paragraph("~ 87-88% (at p=1/N)", style_table),
         Paragraph("<b>&gt; 90.0% (at a=0.01)</b>", style_table_bold)],

        [Paragraph("<b>Throughput at N=35</b>", style_table),
         Paragraph("8.4% (400 frames/stn)", style_table),
         Paragraph("0.0% (herd deadlock)", style_table),
         Paragraph("50.5% (with p=1/N)", style_table),
         Paragraph("<b>55.1% (dominant)</b>", style_table_bold)],

        [Paragraph("<b>Latency at N=35</b>", style_table),
         Paragraph("3637.4 slots", style_table),
         Paragraph("Deadlock (> 13915 slots)", style_table),
         Paragraph("594.9 slots", style_table),
         Paragraph("<b>235.1 slots (-93.5%)</b>", style_table_bold)],

        [Paragraph("<b>Physical Target Media</b>", style_table),
         Paragraph("Wired / Wireless LAN", style_table),
         Paragraph("Wired LAN / Bus", style_table),
         Paragraph("Slotted Bus Systems", style_table),
         Paragraph("<b>Wired Ethernet (802.3)</b>", style_table_bold)],
    ]

    t_matrix = Table(matrix_data, colWidths=[115, 90, 90, 95, 95])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B4F72')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#1B4F72')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9F9')]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Synthesis of Architectural Findings & Cross-Protocol Comparison:</b>", style_h2))
    story.append(Paragraph("1. <b>Carrier Sensing Shrinks Vulnerability:</b> By listening before transmitting, all CSMA protocols reduce the vulnerable period from the full frame transmission time (as in pure ALOHA) down to one-way propagation delay <i>T<sub>p</sub></i>, multiplying channel capacity.", style_bullet))
    story.append(Paragraph("2. <b>CSMA/CD (IEEE 802.3) Dominates Contention:</b> Continuous voltage monitoring (Listen-While-Talk) detects collision superposition &ge; 2.0V within round-trip time <i>2 T<sub>p</sub></i>. Aborting transmissions early saves over 68% wasted airtime per collision, while Truncated BEB dynamically expands up to 1024 slots, sustaining 55.1% throughput and 235.1-slot latency at N=35.", style_bullet))
    story.append(Paragraph("3. <b>p-Persistent CSMA Approximates Optimal Slotted Arbitration:</b> Tuning persistence to <i>p = 1/N</i> statistically paces station access across successive mini-slots, capping collisions at 428 and sustaining 50.5% throughput at N=35. However, lack of collision detection means doomed frames waste full 8.0 ms durations.", style_bullet))
    story.append(Paragraph("4. <b>1-Persistent Herd Deadlock vs. Non-Persistent Backoff Degradation:</b> 1-Persistent's greedy transmission (p = 1.0) guarantees 100% collision deadlock (0.0% throughput) once multiple stations queue frames. Non-Persistent avoids herd deadlock through random backoffs, but its static 16-slot window causes synchronized wake-up collision cascades at high scale, dropping throughput to 8.4%.", style_bullet))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"\n[+] Master Technical Report PDF successfully built: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf_report()
