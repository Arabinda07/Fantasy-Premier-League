"""Script to organize reference excel spreadsheets and archive legacy 2016-2020 files."""
import os
import shutil

REPO_ROOT = r"E:\Fantasy-Premier-League"

# 1. Reference Excel Spreadsheets
ref_dir = os.path.join(REPO_ROOT, "reference", "original_excel")
os.makedirs(ref_dir, exist_ok=True)

extracted_fpl = os.path.join(REPO_ROOT, "FPL 2026-27-20260824T104026Z-1-001", "FPL 2026-27")
if os.path.exists(extracted_fpl):
    for item in os.listdir(extracted_fpl):
        src = os.path.join(extracted_fpl, item)
        dst = os.path.join(ref_dir, item)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)
        print(f"Moved {item} -> reference/original_excel/")
    shutil.rmtree(os.path.join(REPO_ROOT, "FPL 2026-27-20260824T104026Z-1-001"), ignore_errors=True)
    print("Cleaned up FPL 2026-27-20260824T104026Z-1-001")

# 2. Stale Temp Gist Directory
temp_gist = os.path.join(REPO_ROOT, "9a869765af0698fd4fa934ca90029fc8-67e70e7a0e8419139bf9225136e256f7f6d81474")
if os.path.exists(temp_gist):
    shutil.rmtree(temp_gist, ignore_errors=True)
    print("Removed stale temp gist folder")

# 3. Archive Legacy 2016-2020 Files
archive_dir = os.path.join(REPO_ROOT, "archive", "legacy_scrapers_2016_2020")
os.makedirs(archive_dir, exist_ok=True)

legacy_items = [
    "deprecated_script.py",
    "analysis",
    "top_managers.py",
    "top_players.py",
    "schedule.py",
    "gameweek.py",
    "world_cup26_data.py",
    "aggregated_points_goals.py",
    "global_merger.py",
    "utility.py",
    "new_position_checker.py",
    "team_4582_data18_19",
    "lateriser_report_1920.pdf",
    "magnus_report_1920.pdf",
    "vaastav_report_1920.pdf",
]

for item in legacy_items:
    src = os.path.join(REPO_ROOT, item)
    if os.path.exists(src):
        dst = os.path.join(archive_dir, item)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)
        print(f"Archived {item} -> archive/legacy_scrapers_2016_2020/")

print("Cleanup and organization complete.")
