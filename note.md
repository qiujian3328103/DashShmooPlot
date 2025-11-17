New Products (NPI → MP) — My Expertise → Result

Neutron (UXNN)

Method: MSR/STDF deep dives; corner‑lot characterization; bin/limit optimization; FT/EDS correlation.

ROI/Result: 97% yield vs 96% target; stable ramp and handoff.

WhalePeak (UX9U)

Method: Primary PE owner; NPI yield analysis; test‑content deltas; MSR reviews; direct Intel interface and issue closure.

ROI/Result: 96.83% yield vs 96% target; improved customer confidence.

Amlogic S7 (UXWD)

Method: Corner‑lot studies; early‑fail debug; bin strategy refinement; CPM checks post mask change.

ROI/Result: 87% yield vs 86% target; stabilized early production.

Amlogic T6D (UXKO)

Method: EDS/FT analysis; limit tuning; process/test corrections across sites.

ROI/Result: 89% yield vs 88% target; faster NPI → MP transition.

Selected TFT Case Outcomes — Method → ROI

Telechips BIN8151 (PLL): ET↔MSR correlation tied fails to Vtsat↑ from PPID diff at 52.0 HPD2 Anneal → ~14% yield‑loss prevented; ~25 wafers protected (WIP 447).

UXBL BIN146 (10G FT): Program compare + MSR + IP‑block review after new mask → relaxed limit + content fix → ~1.5% yield gain expected.

Amlogic NPI (scan/MBIST): Site‑level diffs via MSR + pattern analysis + program compare → ~1.2% yield improvement potential.

UXC1 FT leakage (VDD GPK): Mapped FT vs reference; isolated GPIO test mismatch; moved check to EDS → DPPM improvement potential ~1081→570.

DX Solutions — Method (how I built it) & ROI (impact)

Nonbump 2.0

Method: Python Dash app; Big Data Explorer ingestion; NocoDB config; auto compute yields/MP compares; CDF/wafer maps/tables; one‑click report; standards for visuals/signatures.

ROI: ~160 engineer‑hours/month saved; backlog ~40→6 cases/month (Oct‑2024); report time ~336 min→~10 min; consistent customer outputs.

SBA Action Tracker

Method: Multi‑user smart‑cloud app; parquet→SQLite3 loader; wafer‑map/bin‑shift visuals; role‑based edits; auto owner emails; audit trail.

ROI: Close‑rate 59%→80%; handling time −26%; manual‑entry errors eliminated; stronger yield protection loop.

OMS Lot Hold Dashboard

Method: Streamlit + smart‑cloud; real‑time holds (MPA/SBL); TAT/release analytics; SBL paretos; interactive wafer maps; scheduled email briefs.

ROI: PE dispo completion 4%→90%; earlier online yield‑health detection; multiple SBL spikes intercepted.

PE MSR Alert System

Method: Automated pipeline (query→DuckDB/S3→SPC/WECO rules→email alerts) + Dash portal for Cpk/shift/correlation.

ROI: 291→59 min/week for 616 params (~6 hrs/week saved); 4 major incidents averted (Q1–Q3 2025) ≈ ~309 wafers protected.

PKDB (PE Knowledge Database)

Method: Central cloud hub for product apps/yield, test‑program versions, bin descriptions (PEBMS); program compare; NPI yield dashboards; version control.

ROI: NPI report 1 hr→2 min; program compare 4 hrs→5 min; reduces stale‑file errors; faster onboarding.

STDF Analyzer (Desktop)

Method: Memory‑efficient batch parse/merge; unstack/stack; MSR/CPM analytics (composite map, CDF, hist, Cpk); export‑ready; local GUI; team training.

ROI: ~288 min→~35 min per case (latest ~10 min typical); reduced Galaxy license dependence (~$25–30k/3 yrs); higher MSR throughput.

MPW Assembly Map Converter (Desktop)

Method: GUI that ingests datalogs, detects logic/SRAM + orientation, outputs DSK‑ready notch‑bottom maps; batch support.

ROI: ~8 hrs→~1 min prep; eliminates wrong‑die risk on time‑critical MPWs.
