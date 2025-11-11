# python tools/BI/looper_dooper_BI.py

import subprocess
import time

# List of Python scripts to run
python_scripts = [

    # # Fruit Intakes API
    # "tools/BI/fetch_fruit_intakes.py",
    # "tools/BI/upload_fruit_intakes_main.py",

#  API Fetches

    "tools/BI/fetch_Vessels.py",
    # "tools/BI/fetch_Vessels_allo.py",
    # "tools/BI/fetch_Vessels_liveMetrics",

    "tools/BI/melt_vessels.py",

    # Workorder Reports
    "tools/BI/fetch_workorders_v7.py",
    "tools/BI/upload_workorders_v7.py",
    "tools/BI/fetch_workorders_v6_singley.py",
    "tools/BI/fetch_workorders_v7_v6_WO_combine_jsons_2025.py",
    "tools/BI/vintrace_work_detail_extract_parcel_weightag_glob.py",
    
#  Playwright Reports

    # Grape Delivery Report
    "tools/BI/vintrace_Grape_Report_with_bookingSummary_playwright.py",
    "tools/BI/vintrace_grape_report_detail.py",

    # Dispatch Console Reports
    "tools/BI/vintrace_dispatch_search_console.py --mode recent --days 7",
    "tools/BI/vintrace_dispatch_search_console.py --mode missing",
    "tools/BI/vintrace_dispatch_search_console.py --mode fetch --csv path/to/missing_dispatches.csv",
    "tools/BI/vintrace_search_console_data.py",

    # Work Detailz Reports
    "tools/BI/vintrace_playwright_work_detailz.py",
    "tools/BI/vintrace_work_detail_extract_parcel_weightag_glob_convert_v2.py",
    "tools/BI/vintrace_work_detail_extract_parcel_weightag_glob_convert_v2_Disp.py",
    "tools/BI/vintrace_work_detail_extract_parcel_weightag_glob_convert_v2_onHand.py",

    # All Barrels Report
    "tools/BI/vintrace_playwright_Barrel_Report.py",

    # Vessels Search Report
    "tools/BI/vintrace_playwright_vessels_report.py",

    # Analysis Export Report & melt 
    "tools/BI/vintrace_playwright_analysis_report.py",
    "tools/BI/vintrace_analysis_process.py",
    

    #Trigger dat Refresh
    "tools/BI/power_auto_trigger.py"
]

# Number of times to loop through the list
num_loops = 1
for i in range(num_loops):
    print(f"Loop {i+1}/{num_loops}")
    for script in python_scripts:
        print(f"Running {script}...")
        result = subprocess.run(["python", script])
        if result.returncode != 0:
            print(f"{script} exited with error code {result.returncode}")
        else:
            print(f"{script} finished successfully.")
    time.sleep(60)  # seconds between loops

print("All loops complete.")