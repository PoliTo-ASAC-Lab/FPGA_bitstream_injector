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

def report_zipper_FreeRTOS():
    # Initializing total counters
    injection_total_cnt = 0
    correct_results_total_cnt = 0
    faulty_results_total_cnt = 0
    hang_processes_total_cnt = 0
    exceptions_total_dict = {
        "XEXC_ID_FSL" : 0,
        "XEXC_ID_UNALIGNED_ACCESS" : 0,
        "XEXC_ID_ILLEGAL_OPCODE" : 0,
        "XEXC_ID_M_AXI_I_EXCEPTION_or_XEXC_ID_IPLB_EXCEPTION" : 0,
        "XEXC_ID_M_AXI_D_EXCEPTION_or_XEXC_ID_DPLB_EXCEPTION" : 0,
        "XEXC_ID_DIV_BY_ZERO" : 0,
        "XEXC_ID_STACK_VIOLATION_or_XEXC_ID_MMU" : 0,
        "XEXC_ID_FPU" : 0
    }
    exception_cnt = 0

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

            exception_cnt += int(report_lines[8].split(" ")[1])
            if DEBUG: print(f"exception cnt {exception_cnt}")

            for i in range(9,len(report_lines)):
                exc_text = report_lines[i].split(" ")[1]
                if exc_text not in exceptions_total_dict.keys():
                    exceptions_total_dict[exc_text] = 0
                exceptions_total_dict[exc_text] += int(report_lines[i].split(" ")[3])


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

        exceptions_percentage = round(100*exception_cnt/injection_total_cnt,2)
        summary.write(f"\nTotal exceptions -> {exception_cnt} [{exceptions_percentage}%]")
        for exc_text in exceptions_total_dict.keys():
            exc_percentage = round(100*exceptions_total_dict[exc_text]/injection_total_cnt,2)
            summary.write(f"\nException[ {exc_text} ]= {exceptions_total_dict[exc_text]} [{exc_percentage}%]")



    print(f"\n...OK - See summary at {summary_filename}")
    print(f"[INFO] Total injections: {injection_total_cnt}")

if __name__ == '__main__':
    report_zipper_FreeRTOS()