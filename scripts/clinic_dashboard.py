#!/usr/bin/env python3
"""
🏥 AI Healthcare System - Interactive Clinic Terminal Dashboard (TUI)
===================================================================
A self-contained, high-fidelity CLI dashboard using ANSI escape codes to 
visualize real-time clinical occupancy, telemetry streams, database pools, 
and machine learning model diagnostics.

Usage:
    python scripts/clinic_dashboard.py
"""

import sys
import time
import random
import os
import math

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_ITALIC = "\033[3m"
CLR_UNDERLINE = "\033[4m"

# Foreground Colors
FG_BLACK = "\033[30m"
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"

# High-Intensity Foreground Colors
FG_HI_BLACK = "\033[90m"
FG_HI_RED = "\033[91m"
FG_HI_GREEN = "\033[92m"
FG_HI_YELLOW = "\033[93m"
FG_HI_BLUE = "\033[94m"
FG_HI_MAGENTA = "\033[95m"
FG_HI_CYAN = "\033[96m"
FG_HI_WHITE = "\033[97m"

# Background Colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# TUI Utilities
def clear_screen():
    sys.stdout.write("\033[2J\033[H")

def move_cursor(y, x):
    sys.stdout.write(f"\033[{y};{x}H")

def hide_cursor():
    sys.stdout.write("\033[?25l")

def show_cursor():
    sys.stdout.write("\033[?25h")

# Mock Clinical Telemetry Class
class TelemetryStream:
    def __init__(self):
        self.tick = 0
        self.beds = [random.choice([True, False, False]) for _ in range(40)] # True = occupied
        self.vitals_history = []
        self.db_connections = 4
        self.cache_hits = 1240
        self.cache_misses = 45
        self.active_consults = 3
        self.errors_logged = 0

    def update(self):
        self.tick += 1
        # Randomly toggle beds (admissions/discharges)
        if random.random() < 0.15:
            bed_idx = random.randint(0, len(self.beds) - 1)
            self.beds[bed_idx] = not self.beds[bed_idx]
            if self.beds[bed_idx]:
                self.active_consults += 1
            else:
                self.active_consults = max(0, self.active_consults - 1)

        # Update cache stats
        if random.random() < 0.8:
            self.cache_hits += random.randint(1, 5)
        else:
            self.cache_misses += random.randint(0, 1)

        # Fluctuating DB connections
        self.db_connections = max(2, min(12, self.db_connections + random.choice([-1, 0, 1])))

        # Generate fake patient vitals feed
        heart_rate = int(72 + 10 * math.sin(self.tick * 0.2) + random.randint(-2, 2))
        sys_bp = int(120 + 8 * math.cos(self.tick * 0.1) + random.randint(-3, 3))
        dia_bp = int(80 + 5 * math.sin(self.tick * 0.1) + random.randint(-2, 2))
        spo2 = max(94, min(100, int(98 + random.choice([-1, 0, 0, 0, 1]))))
        temp = 98.4 + 0.5 * math.sin(self.tick * 0.05) + random.random() * 0.2

        self.vitals_history.append((heart_rate, sys_bp, dia_bp, spo2, temp))
        if len(self.vitals_history) > 10:
            self.vitals_history.pop(0)

# Build the layout grid
def draw_layout():
    clear_screen()
    # Draw top header bar
    sys.stdout.write(f"{BG_BLUE}{FG_HI_WHITE}{CLR_BOLD}" + " 🏥 AI HEALTHCARE PLATFORM - REAL-TIME OPERATION ENGINE ".center(80) + f"{CLR_RESET}\n")
    
    # Grid Borders
    for y in range(2, 24):
        # Left and Right borders
        move_cursor(y, 1)
        sys.stdout.write(f"{FG_HI_BLACK}║{CLR_RESET}")
        move_cursor(y, 80)
        sys.stdout.write(f"{FG_HI_BLACK}║{CLR_RESET}")
    
    # Internal horizontal separations
    move_cursor(10, 1)
    sys.stdout.write(f"{FG_HI_BLACK}" + "╠" + "═"*78 + "╣" + f"{CLR_RESET}")
    
    move_cursor(18, 1)
    sys.stdout.write(f"{FG_HI_BLACK}" + "╠" + "═"*78 + "╣" + f"{CLR_RESET}")

    # Vertical split borders
    for y in range(2, 10):
        move_cursor(y, 45)
        sys.stdout.write(f"{FG_HI_BLACK}║{CLR_RESET}")

    for y in range(10, 18):
        move_cursor(y, 40)
        sys.stdout.write(f"{FG_HI_BLACK}║{CLR_RESET}")

    # Bottom border
    move_cursor(24, 1)
    sys.stdout.write(f"{FG_HI_BLACK}" + "╚" + "═"*78 + "╝" + f"{CLR_RESET}\n")

def render_dashboard(stream):
    # --- Top Left: Operational Census (Beds Grid) ---
    move_cursor(2, 3)
    sys.stdout.write(f"{FG_CYAN}{CLR_BOLD}🩺 INPATIENT WARD CENSUS{CLR_RESET}")
    
    occupied = sum(stream.beds)
    total = len(stream.beds)
    pct = (occupied / total) * 100
    move_cursor(3, 3)
    sys.stdout.write(f"{FG_WHITE}Occupancy: {CLR_BOLD}{occupied}/{total}{CLR_RESET} ({pct:.1f}%)   ")
    
    # Render beds grid
    grid_y = 5
    grid_x = 3
    for i, is_occupied in enumerate(stream.beds):
        if i > 0 and i % 10 == 0:
            grid_y += 1
            grid_x = 3
        move_cursor(grid_y, grid_x)
        if is_occupied:
            sys.stdout.write(f"{BG_RED}{FG_WHITE} B{i+1:02d} {CLR_RESET}")
        else:
            sys.stdout.write(f"{BG_GREEN}{FG_WHITE} B{i+1:02d} {CLR_RESET}")
        grid_x += 4

    # --- Top Right: Systems Telemetry Stats ---
    move_cursor(2, 47)
    sys.stdout.write(f"{FG_CYAN}{CLR_BOLD}🖥️ SYSTEM CLUSTER STATE{CLR_RESET}")
    
    move_cursor(3, 47)
    sys.stdout.write(f"{FG_WHITE}FastAPI Gateway: {FG_GREEN}● ONLINE{CLR_RESET}")
    
    move_cursor(4, 47)
    sys.stdout.write(f"{FG_WHITE}Active DB Pools: {FG_HI_YELLOW}{stream.db_connections}{CLR_RESET}")
    
    hit_rate = (stream.cache_hits / max(1, stream.cache_hits + stream.cache_misses)) * 100
    move_cursor(5, 47)
    sys.stdout.write(f"{FG_WHITE}Redis Cache Hit: {FG_HI_GREEN}{hit_rate:.1f}%{CLR_RESET} ({stream.cache_hits} hits)")
    
    move_cursor(6, 47)
    sys.stdout.write(f"{FG_WHITE}LangGraph Agent: {FG_GREEN}IDLE / MONITORING{CLR_RESET}")

    move_cursor(7, 47)
    sys.stdout.write(f"{FG_WHITE}RAG Vector Store: {FG_HI_BLUE}turbovec SIMD Active{CLR_RESET}")

    move_cursor(8, 47)
    sys.stdout.write(f"{FG_WHITE}Exception Masking: {FG_GREEN}● HIPAA SECURE{CLR_RESET}")

    # --- Middle Left: Live ICU Vitals Streaming ---
    move_cursor(10, 3)
    sys.stdout.write(f"{FG_CYAN}{CLR_BOLD}📡 LIVE PATIENT VITAL CHANNELS (BED 07){CLR_RESET}")
    
    if stream.vitals_history:
        hr, sbp, dbp, spo2, temp = stream.vitals_history[-1]
        
        # Color code HR status
        hr_color = FG_GREEN if 60 <= hr <= 100 else FG_HI_RED
        spo2_color = FG_GREEN if spo2 >= 95 else FG_HI_RED
        
        move_cursor(12, 3)
        sys.stdout.write(f"{FG_WHITE}Heart Rate (PR):    {hr_color}{CLR_BOLD}{hr} bpm{CLR_RESET}   ")
        move_cursor(13, 3)
        sys.stdout.write(f"{FG_WHITE}Blood Pressure:     {FG_GREEN}{sbp}/{dbp} mmHg{CLR_RESET}   ")
        move_cursor(14, 3)
        sys.stdout.write(f"{FG_WHITE}Oxygen Sat (SpO2):  {spo2_color}{CLR_BOLD}{spo2}%{CLR_RESET}      ")
        move_cursor(15, 3)
        sys.stdout.write(f"{FG_WHITE}Body Temperature:   {FG_GREEN}{temp:.1f} °F{CLR_RESET}   ")
    
    # --- Middle Right: ML Inference Diagnostics ---
    move_cursor(10, 42)
    sys.stdout.write(f"{FG_CYAN}{CLR_BOLD}🧠 ACTIVE CLINICAL ML PIPELINES{CLR_RESET}")
    
    models = [
        ("Diabetes XGBoost", 0.8287, FG_HI_BLUE),
        ("Heart XGBoost", 0.8467, FG_HI_GREEN),
        ("Liver XGBoost", 0.9799, FG_HI_CYAN),
        ("Kidney XGBoost", 0.9912, FG_HI_MAGENTA),
        ("Lungs XGBoost", 0.9250, FG_HI_YELLOW)
    ]
    
    for idx, (name, auc, color) in enumerate(models):
        move_cursor(12 + idx, 42)
        # Draw a little text bar chart representing AUC
        bar_len = int(auc * 15)
        bar_str = "█" * bar_len + "░" * (15 - bar_len)
        sys.stdout.write(f"{FG_WHITE}{name:16}: {color}{bar_str}{CLR_RESET} {CLR_BOLD}{auc:.4f}{CLR_RESET}")

    # --- Bottom: Real-Time Event & Audit Log Stream ---
    move_cursor(18, 3)
    sys.stdout.write(f"{FG_CYAN}{CLR_BOLD}📑 AUDIT TRAIL & TRANSACTION LOGS{CLR_RESET}")
    
    events = [
        f"[{time.strftime('%H:%M:%S')}] [SECURE] Inbound REST call verified under X-Request-ID.",
        f"[{time.strftime('%H:%M:%S')}] [AUDIT] Clinician reviewed and validated Diabetes diagnosis override.",
        f"[{time.strftime('%H:%M:%S')}] [COMPLIANCE] Patient EHR exported to FHIR R4 JSON Bundle.",
        f"[{time.strftime('%H:%M:%S')}] [RAG] Retrieved medical context for Lungs check in 2.4ms.",
        f"[{time.strftime('%H:%M:%S')}] [TELEMETRY] Broadcasted clinic census status over WebSocket.",
    ]
    
    # Show last 4 events based on clock ticks
    for idx in range(4):
        move_cursor(19 + idx, 3)
        ev_idx = (stream.tick + idx) % len(events)
        # Clear line before writing
        sys.stdout.write("\033[K")
        sys.stdout.write(f"{FG_HI_BLACK}{events[ev_idx][:74]}{CLR_RESET}")

    # Footer navigation
    move_cursor(23, 3)
    sys.stdout.write(f"{FG_HI_WHITE}{CLR_ITALIC}Press [Ctrl+C] to exit the dashboard visualization safely.{CLR_RESET}")
    sys.stdout.flush()

def main():
    stream = TelemetryStream()
    hide_cursor()
    try:
        draw_layout()
        while True:
            stream.update()
            render_dashboard(stream)
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        clear_screen()
        print("🏥 Clinical dashboard safely shutdown.")

if __name__ == "__main__":
    main()
