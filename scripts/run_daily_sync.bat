@echo off
REM Quick Batch Runner for FPL Daily Live Sync
cd /d "E:\Fantasy-Premier-League"
echo ==============================================================================
echo Running Daily FPL Live Pipeline Sync & Price Velocity Tracker...
echo ==============================================================================
python -m model.pipeline_automation --season 2026-27 --mode sync
echo ==============================================================================
echo Daily sync completed!
echo ==============================================================================
pause
