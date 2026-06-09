"""
PDF Health Report Generator
============================
Generates downloadable PDF health reports with longitudinal trend charts.

Charts included (when data is available):
  - Risk Assessment History  — bar chart of assessment outcomes over time
  - Vital Signs Trends       — line charts for heart rate, BP, SpO2, temperature

Dependencies: fpdf2 (core), matplotlib (charts — gracefully skipped if absent).
"""
import io
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fpdf import FPDF

logger = logging.getLogger(__name__)

# Matplotlib is optional — charts are skipped gracefully if not installed
try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend, safe in server environments
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    _MPL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MPL_AVAILABLE = False
    logger.warning("matplotlib not installed — trend charts will be omitted from PDF reports.")


# ---------------------------------------------------------------------------
# Chart generation helpers
# ---------------------------------------------------------------------------

def _fig_to_png_bytes(fig: "Figure") -> bytes:
    """Render a matplotlib Figure to PNG bytes and close the figure."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    data = buf.read()
    plt.close(fig)
    return data


def _parse_date(value: Any) -> Optional[datetime]:
    """Try to parse a date value from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, "strftime"):
        return datetime(value.year, value.month, value.day)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value)[:19], fmt)
        except ValueError:
            continue
    return None


def _chart_risk_assessment_history(health_records: List[Dict[str, Any]]) -> Optional[bytes]:
    """
    Bar chart showing assessment outcomes (High Risk vs Low Risk) per record type
    over time.  Returns PNG bytes or None if data is insufficient.
    """
    if not _MPL_AVAILABLE or not health_records:
        return None

    # Group by record type, count high vs low risk
    type_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"high": 0, "low": 0})
    dated_records = []
    for r in health_records:
        dt = _parse_date(r.get("timestamp"))
        prediction = str(r.get("prediction", "")).lower()
        rtype = str(r.get("record_type", "Unknown")).title()
        is_high = any(kw in prediction for kw in ("risk", "positive", "yes", "detected", "high"))
        if dt:
            dated_records.append((dt, rtype, is_high))
        type_counts[rtype]["high" if is_high else "low"] += 1

    if not type_counts:
        return None

    types = sorted(type_counts.keys())
    high_counts = [type_counts[t]["high"] for t in types]
    low_counts = [type_counts[t]["low"] for t in types]
    x = range(len(types))

    fig, ax = plt.subplots(figsize=(7, 3.5))
    width = 0.35
    bars_low = ax.bar([i - width / 2 for i in x], low_counts, width,
                      label="Low Risk", color="#16a34a", alpha=0.85)
    bars_high = ax.bar([i + width / 2 for i in x], high_counts, width,
                       label="High Risk", color="#dc2626", alpha=0.85)

    ax.set_xlabel("Assessment Type", fontsize=9)
    ax.set_ylabel("Number of Assessments", fontsize=9)
    ax.set_title("Risk Assessment Summary by Type", fontsize=11, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(types, fontsize=8, rotation=20, ha="right")
    ax.legend(fontsize=8)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    return _fig_to_png_bytes(fig)


def _chart_assessment_timeline(health_records: List[Dict[str, Any]]) -> Optional[bytes]:
    """
    Scatter/timeline chart showing each assessment as a dot on a time axis,
    coloured by risk level.  Returns PNG bytes or None if fewer than 2 dated records.
    """
    if not _MPL_AVAILABLE or not health_records:
        return None

    dated = []
    for r in health_records:
        dt = _parse_date(r.get("timestamp"))
        if not dt:
            continue
        prediction = str(r.get("prediction", "")).lower()
        rtype = str(r.get("record_type", "Unknown")).title()
        is_high = any(kw in prediction for kw in ("risk", "positive", "yes", "detected", "high"))
        dated.append((dt, rtype, is_high))

    if len(dated) < 2:
        return None

    dated.sort(key=lambda x: x[0])
    dates = [d[0] for d in dated]
    types = [d[1] for d in dated]
    colors = ["#dc2626" if d[2] else "#16a34a" for d in dated]

    # Assign y-positions per unique type
    unique_types = sorted(set(types))
    type_y = {t: i for i, t in enumerate(unique_types)}
    ys = [type_y[t] for t in types]

    fig, ax = plt.subplots(figsize=(7, max(2.5, len(unique_types) * 0.7 + 1.5)))
    ax.scatter(dates, ys, c=colors, s=70, zorder=3, alpha=0.9)
    ax.set_yticks(list(range(len(unique_types))))
    ax.set_yticklabels(unique_types, fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=30, ha="right")
    ax.set_xlabel("Date", fontsize=9)
    ax.set_title("Assessment Timeline", fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#16a34a", markersize=8, label="Low Risk"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#dc2626", markersize=8, label="High Risk"),
    ]
    ax.legend(handles=legend_elements, fontsize=8, loc="upper left")
    fig.tight_layout()

    return _fig_to_png_bytes(fig)


def _chart_vitals_trends(vital_records: List[Dict[str, Any]]) -> Optional[bytes]:
    """
    Multi-panel line chart for vital signs over time:
    Heart Rate, Blood Pressure (systolic/diastolic), SpO2, Temperature.
    Returns PNG bytes or None if insufficient data.
    """
    if not _MPL_AVAILABLE or not vital_records:
        return None

    # Parse and sort by date
    rows = []
    for v in vital_records:
        dt = _parse_date(v.get("observed_at") or v.get("timestamp"))
        if not dt:
            continue
        rows.append({
            "dt": dt,
            "hr": v.get("heart_rate"),
            "sbp": v.get("systolic_bp"),
            "dbp": v.get("diastolic_bp"),
            "spo2": v.get("spo2"),
            "temp": v.get("temperature_c"),
        })

    if len(rows) < 2:
        return None

    rows.sort(key=lambda r: r["dt"])
    dates = [r["dt"] for r in rows]

    # Determine which panels have data
    panels = []
    if any(r["hr"] is not None for r in rows):
        panels.append(("Heart Rate (bpm)", [r["hr"] for r in rows], "#3b82f6", None))
    if any(r["sbp"] is not None or r["dbp"] is not None for r in rows):
        panels.append(("Blood Pressure (mmHg)", [r["sbp"] for r in rows], "#ef4444",
                        [r["dbp"] for r in rows]))
    if any(r["spo2"] is not None for r in rows):
        panels.append(("SpO2 (%)", [r["spo2"] for r in rows], "#8b5cf6", None))
    if any(r["temp"] is not None for r in rows):
        panels.append(("Temperature (°C)", [r["temp"] for r in rows], "#f59e0b", None))

    if not panels:
        return None

    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(7, n * 2.2 + 0.5), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, (label, values, color, values2) in zip(axes, panels):
        valid_dates = [d for d, v in zip(dates, values) if v is not None]
        valid_vals = [v for v in values if v is not None]

        if valid_dates:
            ax.plot(valid_dates, valid_vals, color=color, linewidth=1.8,
                    marker="o", markersize=4, label=label.split(" (")[0])
            ax.fill_between(valid_dates, valid_vals, alpha=0.12, color=color)

        if values2 is not None:
            valid_dates2 = [d for d, v in zip(dates, values2) if v is not None]
            valid_vals2 = [v for v in values2 if v is not None]
            if valid_dates2:
                ax.plot(valid_dates2, valid_vals2, color="#f97316", linewidth=1.8,
                        marker="s", markersize=4, linestyle="--", label="Diastolic")
                ax.legend(fontsize=7, loc="upper right")

        ax.set_ylabel(label, fontsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="y", labelsize=7)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=30, ha="right")
    axes[-1].tick_params(axis="x", labelsize=7)
    fig.suptitle("Vital Signs Longitudinal Trends", fontsize=11, fontweight="bold", y=1.01)
    fig.tight_layout()

    return _fig_to_png_bytes(fig)


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------

class HealthReportPDF(FPDF):
    """Custom PDF class with healthcare branding."""

    def header(self):
        """Add header to each page."""
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(59, 130, 246)  # Blue
        self.cell(0, 10, "AI Healthcare System", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Personal Health Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        """Add footer to each page."""
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0, 5,
            "This report is AI-generated and should not replace professional medical advice.",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        self.cell(
            0, 5,
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Page {self.page_no()}",
            align="C",
        )

    def _embed_chart(self, png_bytes: bytes, title: str, width: float = 170.0) -> None:
        """
        Embed a PNG chart into the PDF.
        Writes a labelled section heading then the image inline.
        """
        # Section heading
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 30, 30)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")

        # Write PNG bytes to a temporary in-memory buffer readable by fpdf2
        buf = io.BytesIO(png_bytes)
        # Calculate height to maintain aspect ratio at target width
        # fpdf2 accepts a file-like object directly
        x = self.get_x()
        y = self.get_y()
        self.image(buf, x=x, y=y, w=width)
        # Advance cursor past the image (approximate height = width * 0.55 for typical charts)
        self.set_y(y + width * 0.55)
        self.ln(4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_health_report(
    user_name: str,
    user_profile: Dict[str, Any],
    health_records: List[Dict[str, Any]],
    vital_records: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    """
    Generate a PDF health report with longitudinal trend charts.

    Args:
        user_name:      User's full name.
        user_profile:   Dict with height, weight, dob, blood_type, etc.
        health_records: List of health assessment records (record_type, prediction, timestamp).
        vital_records:  Optional list of vital sign observations
                        (heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c,
                        observed_at / timestamp).

    Returns:
        bytes: PDF file content.
    """
    vital_records = vital_records or []

    pdf = HealthReportPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # ── User Info ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, f"Health Report for {user_name}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)

    height = user_profile.get("height", "N/A")
    weight = user_profile.get("weight", "N/A")
    dob = user_profile.get("dob", "N/A")
    blood_type = user_profile.get("blood_type", "N/A")

    bmi_str = "N/A"
    if height and weight and height != "N/A" and weight != "N/A":
        try:
            h_m = float(height) / 100
            bmi = round(float(weight) / (h_m ** 2), 1)
            bmi_str = str(bmi)
        except Exception:
            pass

    pdf.cell(0, 7, f"Date of Birth: {dob}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Height: {height} cm | Weight: {weight} kg | BMI: {bmi_str}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Blood Type: {blood_type}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # ── Health Assessment Table ────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Health Assessment History", new_x="LMARGIN", new_y="NEXT")

    if not health_records:
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 7, "No health assessments recorded yet.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 8, "Date", border=1, fill=True)
        pdf.cell(50, 8, "Assessment Type", border=1, fill=True)
        pdf.cell(80, 8, "Result", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        for record in health_records[:20]:
            date_str = record.get("timestamp", "N/A")
            if hasattr(date_str, "strftime"):
                date_str = date_str.strftime("%Y-%m-%d")

            record_type = record.get("record_type", "Unknown")
            prediction = record.get("prediction", "N/A")

            if any(kw in str(prediction).lower()
                   for kw in ("risk", "positive", "yes", "detected", "high")):
                pdf.set_text_color(220, 38, 38)
            else:
                pdf.set_text_color(22, 163, 74)

            pdf.cell(50, 7, str(date_str)[:10], border=1)
            pdf.cell(50, 7, str(record_type), border=1)
            pdf.cell(80, 7, str(prediction)[:40], border=1, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(60, 60, 60)

    pdf.ln(10)

    # ── Trend Charts ──────────────────────────────────────────────────────
    charts_added = 0

    # 1. Risk Assessment Summary (bar chart)
    bar_png = _chart_risk_assessment_history(health_records)
    if bar_png:
        if pdf.get_y() > 200:
            pdf.add_page()
        if charts_added == 0:
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 10, "Longitudinal Trends", new_x="LMARGIN", new_y="NEXT")
        pdf._embed_chart(bar_png, "Risk Assessment Summary by Type")
        charts_added += 1

    # 2. Assessment Timeline (scatter)
    timeline_png = _chart_assessment_timeline(health_records)
    if timeline_png:
        if pdf.get_y() > 210:
            pdf.add_page()
        pdf._embed_chart(timeline_png, "Assessment Timeline")
        charts_added += 1

    # 3. Vital Signs Trends (multi-panel line chart)
    vitals_png = _chart_vitals_trends(vital_records)
    if vitals_png:
        if pdf.get_y() > 180:
            pdf.add_page()
        if charts_added == 0:
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 10, "Longitudinal Trends", new_x="LMARGIN", new_y="NEXT")
        pdf._embed_chart(vitals_png, "Vital Signs Longitudinal Trends", width=160.0)
        charts_added += 1

    if charts_added == 0 and _MPL_AVAILABLE:
        # matplotlib available but no data — show a note
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0, 7,
            "Trend charts will appear here once sufficient longitudinal data is recorded.",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(4)

    pdf.ln(6)

    # ── Recommendations ───────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "General Health Recommendations", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    for rec in [
        "- Schedule regular check-ups with your healthcare provider",
        "- Maintain a balanced diet rich in fruits and vegetables",
        "- Exercise for at least 30 minutes daily",
        "- Get 7-8 hours of quality sleep each night",
        "- Stay hydrated — drink 8 glasses of water daily",
        "- Monitor your vitals regularly and track changes",
    ]:
        pdf.cell(0, 6, rec, new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
