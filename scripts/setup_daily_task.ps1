# PowerShell Script to register a native Windows Scheduled Task for Daily FPL Sync
# Runs every day at 06:00 UTC (or system local time)

$TaskName = "FPL_Daily_Data_Pipeline_Sync"
$PythonPath = (Get-Command python).Source
$RepoRoot = "E:\Fantasy-Premier-League"
$Arguments = "-m model.pipeline_automation --season 2026-27 --mode sync"

Write-Host "Creating Windows Scheduled Task: $TaskName..." -ForegroundColor Cyan
Write-Host "Python Path: $PythonPath"
Write-Host "Working Directory: $RepoRoot"

# Define the scheduled action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $Arguments -WorkingDirectory $RepoRoot

# Define the trigger (Daily at 06:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:00AM"

# Task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Register or update the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily Fantasy Premier League Data Pipeline Sync, Price Velocity Tracking, and Points Prediction Refresh" -Force

Write-Host "✓ Windows Scheduled Task '$TaskName' registered successfully!" -ForegroundColor Green
Write-Host "It will run automatically every morning at 06:00 AM."
