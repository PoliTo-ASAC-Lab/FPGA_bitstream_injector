"""
0    --FUNCTIONAL_ANALYSIS--
1 performed_injections= 77
2     [aborted_injections= 23]
3 correct_results= 66
4 faulty_results= 3
5 faulty_results_bitstreams= [18, 49, 69]
6 hang_processes= 8
7 hang_processes_bitstreams= [13, 31, 37, 44, 48, 65, 68, 84]
"""
from glob import glob
import datetime
import os
from os import path

DEBUG = False

def report_zipper():
    # Initializing total counters
    injection_total_cnt = 0
    correct_results_total_cnt = 0
    faulty_results_total_cnt = 0
    hang_processes_total_cnt = 0


    summary_folder = f"./fi_reports/SUMMARIES/"
    if not path.exists(summary_folder):
        print(f"\tCreated {summary_folder} !")
        os.mkdir(summary_folder)  
    
    # Parsing files
    print("\nParsing files...")

    reports_filenames = glob("./fi_reports/FI_campaign_*.txt")
    for r_filename in reports_filenames:
        print(f"\t{r_filename}")

        with open(r_filename) as report:
            report_lines = report.read().splitlines() #lines of file are now accessible in this list

            injection_total_cnt += int(report_lines[1].split(" ")[1]) 
            if DEBUG: print(f"inj cnt {injection_total_cnt}")

            correct_results_total_cnt += int(report_lines[3].split(" ")[1]) 
            if DEBUG: print(f"correct cnt {correct_results_total_cnt}")

            faulty_results_total_cnt += int(report_lines[4].split(" ")[1]) 
            if DEBUG: print(f"faulty cnt {faulty_results_total_cnt}")

            hang_processes_total_cnt += int(report_lines[6].split(" ")[1]) 
            if DEBUG: print(f"hang cnt {hang_processes_total_cnt}")



    # Printing summary
    print("\nPrinting summary...",end="")

    timestamp = (datetime.datetime.now()).strftime("%Y-%m-%d@%H%M")
    summary_filename = f"./fi_reports/SUMMARIES/uBlaze_FI_SUMMARY_{timestamp}.txt"


    with open(summary_filename,"w+") as summary:
        summary.write("Files involved in this summary:\n")
        for filename in reports_filenames:
            summary.write("\t"+filename+"\n")

        summary.write(f"\nTotal injected bitflips = {injection_total_cnt}")

        summary.write("\n\n\t--- FUNCTIONAL ANALYSIS ---")
        
        correct_results_percentage = round(100*correct_results_total_cnt/injection_total_cnt,2)
        summary.write(f"\nCorrect results -> {correct_results_total_cnt} [{correct_results_percentage}%]")
        
        faulty_results_percentage = round(100*faulty_results_total_cnt/injection_total_cnt,2)
        summary.write(f"\nFaulty results -> {faulty_results_total_cnt} [{faulty_results_percentage}%]")        

        hang_processes_percentage = round(100*hang_processes_total_cnt/injection_total_cnt,2)
        summary.write(f"\nMicroBlaze halted -> {hang_processes_total_cnt} [{hang_processes_percentage}%]")



    print(f"\n...OK - See summary at {summary_filename}")
    print(f"[INFO] Total injections: {injection_total_cnt}")


if __name__ == '__main__':
    report_zipper()