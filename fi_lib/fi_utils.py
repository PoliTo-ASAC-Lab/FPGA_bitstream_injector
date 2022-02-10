import os
from os import path
import random
import sys
import signal
import subprocess
import time
import shlex
import re
import datetime
import wexpect

from fi_lib.bitman import bitflip
from fi_lib.crc32 import CRC32_hash
from fi_lib.fi_utils import *

def clear_folders():
    print("INFO: Clearing/Creating folders")

    faulty_bitstreams_folder = "./faulty_bitstreams/"
    if (path.exists(faulty_bitstreams_folder)):
        for filename in os.listdir(faulty_bitstreams_folder):
            filepath = ""
            filepath = os.path.join(faulty_bitstreams_folder, filename)
            #print(f"filepath:{filepath}")
            if os.path.isfile(filepath):
                os.remove(filepath)
    else:
        print("\tCreated ./faulty_bitstreams/ !")
        os.mkdir(faulty_bitstreams_folder)


    results_folder = "./faulty_bitstreams/uB_results"
    if (path.exists(results_folder)):
        for filename in os.listdir(results_folder):
            filepath = ""
            filepath = os.path.join(results_folder, filename)
            # print(f"filepath:{filepath}")
            os.remove(filepath)
    else:
        print(f"\tCreated {results_folder} !")
        os.mkdir(results_folder)

def wait_exec(t):
    print("\n\nLetting processes execute for ",end="")
    for i in range(0,t):
        print(f"...{t-i}")
        time.sleep(1)
    print("...GO\n")

def bitflip_injection(golden_bitstream, injection_num):
    ### KCU040 INFORMATION
    ### Total Frames: 32530
    ### Words per frame: 123
    ### Bytes per word: 4

    total_frames = 32530
    words_per_frame = 123
    bytes_per_word = 4
    starting_frame = 0

    # Searching for injectable part of the bitstream
    start_byte, end_byte = bitstream_analyzer(golden_bitstream)

    # Reading golden content
    with open(f"{golden_bitstream}", "rb") as golden_file:
        golden_content = golden_file.read()
    golden_file.close()
    i=0
    for i in range(0, int(injection_num)):

        ########## Selective Injection Coordinates - Method 1 ##########

        ## Limits
        x_low = 11828# in frames (== X-pixels in pbm image)
        x_high = 11828+1004
        y_low = 2016/8 # in bytes (== Y-pixels in pbm image/8)
        y_high = words_per_frame * bytes_per_word

        ## Injection
        random_frame = random.randint(x_low,x_high)
        random_byte = random.randint(y_low,y_high)
        x_cord = start_byte + (starting_frame + random_frame) * words_per_frame * bytes_per_word
        y_cord = random_byte

        ########## Selective Injection Coordinates - Method 2 ##########
        coordinates_are_good = True
        while (coordinates_are_good == False):
            coordinates_are_good = True
            random_frame = random.randint(0,total_frames)
            random_byte = random.randint(0,words_per_frame*bytes_per_word)
            random_word = random_byte/32
            x_cord = start_byte + (starting_frame + random_frame) * words_per_frame * bytes_per_word
            y_cord = random_byte

            # negative constraints set 1
            if((random_frame < 11724 or random_frame > 13000) or (random_word < 50)):
                coordinates_are_good = False            

            # negative constraints set 2
            # negative constraints set 3
            # negative constraints set 4
            # negative constraints set 5
            # negative constraints set 6
            # negative constraints set 7
        
        print(f"DEBUG.:|Injection#{i}: x={random_frame}th frame, y={random_byte}th byte={(int)(random_byte/4)}th word")



        byte_cord = x_cord + y_cord
        bit_cord = random.randint(0, 7)

        number = golden_content[byte_cord]
        faulty_number = bitflip(number, bit_cord)
        faulty_bin_content = bytearray(golden_content)
        faulty_bin_content[byte_cord] = faulty_number
        faulty_bitstream = f"./faulty_bitstreams/inj_{i}.bit"
        #print (f"Injection#{i} is at #{byte_cord}, frame#{int(byte_cord/(123*4))} | golden byte={golden_content [byte_cord]} | faulty byte={faulty_bin_content[byte_cord]}")

        with open(faulty_bitstream, "wb") as faulty_file:
            faulty_file.write(faulty_bin_content)
        faulty_file.close()

        if not((i+1)%50) : print(f"\tDONE {i+1} injections",end="\r")
    print(f"\tDONE {i+1} injections")
    print("\t...OK")

def bitstream_analyzer(bitstream):
    with open(f"{bitstream}", "rb") as bitstream:
        bitstream_content = bitstream.read()
    bitstream.close()

    # In KU040 bitstream configuration data are put after 30004000 503D0DA6 data words
    start_pattern_match = re.search(b'\x30\x00\x40\x00\x50\x3D\x0D\xA6', bitstream_content) 

    if(start_pattern_match == None):
        exit("Check bitstream, cause no start_pattern_match has been found!")
    else:
        start_byte = start_pattern_match.start()+4
        end_byte = start_byte+(4001190*4) 
        # cause 4,001,190 is the number of bitstream configuration data word in KU040
        # and 4 are the bytes composing each word

        #print(f"\n\n start byte is #{start_byte}") #_debug 
        #print(f"\n\n end byte is #{end_byte}") #_debug
    #print(f"\n\nstarting --> {bitstream_content[start_byte:start_byte+16].hex()}") #_debug
    #print(f"\n\nending --> {bitstream_content[end_byte:end_byte+16].hex()}") #_debug
    return start_byte, end_byte

def getXSCT_pid(XSCTp, debug = True):
    XSCTp.sendline('puts [pid] ; join [concat "XSCT_" "DONE"] ""')
    XSCTp.expect('XSCT_DONE')
    pid = (int)((XSCTp.before).splitlines()[-1])
    if debug: print(pid)
    return pid

def XSCTcommunicate(child, command, debug=False):
    #!!!! child must be a wexpect.spawn object
    xsct_prompt = ['XSCT_DONE', 'XSCT_ERROR', wexpect.TIMEOUT]
    child.sendline(command)
    if debug: 
        print(child.before)
    xsct_reply_id = child.expect(xsct_prompt)
    if xsct_reply_id != 0: #an error occurred
        print(f"Error occurred in XSCT while trying to execute:\n\t{command}")
        return False
    else:
        print(f"\n\t\t\t XSCT replied: {xsct_prompt[xsct_reply_id]}")
        return True

def FPGA_prog_and_exec(XSCTproc, app_listener, bitstream_file, ELF_file, app_out_file, DEBUG=False):
    
    if DEBUG: print("Exec1")
    if not XSCTcommunicate(XSCTproc, 'if { [catch {targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2"} }] } {join [concat "XSCT_" "ERROR"] ""} else { join [concat "XSCT_" "DONE"] ""}'): return False# selecting microblaze as target
    
    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec2")
    XSCTcommunicate(XSCTproc, 'rst -processor; rst -system; rst -srst; join [concat "XSCT_" "DONE"] ""')#' puts "XSCT_DONE"') # reset of the system

    if DEBUG: time.sleep(2)
    XSCTcommunicate(XSCTproc, 'after 1000; join [concat "XSCT_" "DONE"] ""')

    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec3")
    if not XSCTcommunicate(XSCTproc, f'while {{ [catch {{fpga -file "{bitstream_file}" -no-revision-check -skip-compatibility-check}}] }} {{ rst -system }}; join [concat "XSCT_" "DONE"] "" '): return False # programming the FPGA

    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec4")
    if not XSCTcommunicate(XSCTproc, f'while {{ [catch {{dow {ELF_file}}}] }} {{rst -system}}; join [concat "XSCT_" "DONE"] ""'): return False# loading ELF file
    
    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec5")
    app_listener.do_async_listen(app_out_file) # starting app_listener
    
    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec6")
    if not XSCTcommunicate(XSCTproc,'if { [catch { con }] } {join [concat "XSCT_" "ERROR"] ""} else { join [concat "XSCT_" "DONE"] ""}'): return False # starting app execution
    
    app_listener.async_listener_thread.join() # waiting app conclusion (seeking end keyword) or timeout
    
    
    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec7")
    if not XSCTcommunicate(XSCTproc, 'if { [catch { rst -processor }] } {join [concat "XSCT_" "ERROR"] ""} else { join [concat "XSCT_" "DONE"] ""}'): return False # reset of the system

    if DEBUG: time.sleep(2)
    if DEBUG: print("Exec8")
    app_listener.connection.reset_output_buffer()
    app_listener.connection.reset_input_buffer()


    return True
    
def functional_analysis(injection_num, report_filepath):
    """
    Performs thr functional analysis by comparing the CRC32 hashes of file
    ./faulty_bitstreams/uB_results/golden_uB_result.dat
    with file
    ./bitflipped_binaries/results/uB_result_{i}.dat
    """
    verbose_report = True
    faulty_cnt = 0
    faulty_l = [] 
    hang_process_cnt = 0
    hang_process_l = []
    aborted_cnt = 0
    aborted_l = []

    # Reading list of aborted injections (due to link failure or anything else)
    aborted_injections_file_path = "./faulty_bitstreams/uB_results/aborted.txt"
    if (path.exists(aborted_injections_file_path)):
        aborted_injections_file = open(aborted_injections_file_path, "r+")
        aborted_injections_file_content = aborted_injections_file.read()
        for proc_num in aborted_injections_file_content.splitlines():
            if proc_num != "":
                aborted_cnt += 1
                aborted_l.append(int(proc_num))

    # Reading list of hang processes
    hang_process_file_path = "./faulty_bitstreams/uB_results/hang_processes.txt"
    if (path.exists(hang_process_file_path)):
        hang_process_file = open(hang_process_file_path, "r+")
        hang_process_file_content = hang_process_file.read()
        for proc_num in hang_process_file_content.splitlines():
            if proc_num != "":
                hang_process_cnt += 1
                hang_process_l.append(int(proc_num))

    # Hashing golden results
    gold_res_filename = f"./faulty_bitstreams/uB_results/golden_uB_result.dat"
    golden_hash = CRC32_hash(gold_res_filename) # GOLDEN RESULTS

    # Comparing with other results
    for i in range(0,int(injection_num)):
        faulty_res_filename = f"./faulty_bitstreams/uB_results/uB_result_{i}.dat"
        faulty_hash = CRC32_hash(faulty_res_filename)
        if faulty_hash != golden_hash:
            if (i not in hang_process_l) and (i not in aborted_l):
                faulty_cnt += 1
                faulty_l.append(i)


    # ******* Printing the results *******
    out_file = open(report_filepath,"a+")
    out_file.write(f"\t--FUNCTIONAL_ANALYSIS--")
    out_file.write(f"\nperformed_injections= {injection_num-aborted_cnt}")    
    out_file.write(f"\n\t[aborted_injections= {aborted_cnt}]")
    out_file.write(f"\ncorrect_results= {injection_num -faulty_cnt -hang_process_cnt -aborted_cnt}")    
    out_file.write(f"\nfaulty_results= {faulty_cnt}")
    out_file.write(f"\nfaulty_results_bitstreams= {faulty_l}")    
    out_file.write(f"\nhang_processes= {hang_process_cnt}")
    out_file.write(f"\nhang_processes_bitstreams= {hang_process_l}")

    out_file.close()

def functional_analysis_FreeRTOS(injection_num, report_filepath, aborted_l, r_seed):
    """
    Performs thr functional analysis by comparing the CRC32 hashes of file
    ./faulty_bitstreams/uB_results/golden_uB_result.dat
    with file
    ./bitflipped_binaries/results/uB_result_{i}.dat
    """

    """
    Output Classification:
        1) Correct: execution ends ("with correct results" NOT CHECKED YET)
        2) Hang: execution stops without exception occurrence
        3) Exception: execution stops with exception occurrence
            Example of exception signature: "---- Exception: XEXC_ID_FSL ----"
        4) Faulty/SDE: execution terminates with faulty results 
    """
    print(aborted_l)

    verbose_report = True
    faulty_cnt = 0
    faulty_l = [] 
    hang_process_cnt = 0
    hang_process_l = []
    #aborted_l = [] # PASSED VIA PARAMS
    aborted_cnt = len(aborted_l) 
    exceptions_dict = {
        "XEXC_ID_FSL" : 0,
        "XEXC_ID_UNALIGNED_ACCESS" : 0,
        "XEXC_ID_ILLEGAL_OPCODE" : 0,
        "XEXC_ID_M_AXI_I_EXCEPTION_or_XEXC_ID_IPLB_EXCEPTION" : 0,
        "XEXC_ID_M_AXI_D_EXCEPTION_or_XEXC_ID_DPLB_EXCEPTION" : 0,
        "XEXC_ID_DIV_BY_ZERO" : 0,
        "XEXC_ID_STACK_VIOLATION_or_XEXC_ID_MMU" : 0,
        "XEXC_ID_FPU" : 0
    }
    exception_process_l = []
    exception_cnt = 0

    # !!!! NOT USED !!!! Reading list of aborted injections (due to link failure or anything else)
    aborted_injections_file_path = "./faulty_bitstreams/uB_results/aborted.txt"
    if (path.exists(aborted_injections_file_path)):
        aborted_injections_file = open(aborted_injections_file_path, "r+")
        aborted_injections_file_content = aborted_injections_file.read()
        for proc_num in aborted_injections_file_content.splitlines():
            if proc_num != "":
                aborted_cnt += 1
                aborted_l.append(int(proc_num))

            
    # Checking completion (TBD: and correctness)
    # Golden output
    gold_res_filename = f"./faulty_bitstreams/uB_results/golden_uB_result.dat"
    done_flag_1 = False
    done_flag_2 = False
    golden_content = open(gold_res_filename,"r+")
    for line in golden_content.read().splitlines():
        splitted_line = line.split()
        print
        if (not done_flag_1) and ("DONE_1" in splitted_line):
            done_flag_1 = True
        if (not done_flag_2) and ("DONE_2" in splitted_line):
            done_flag_2 = True
        if done_flag_1 and done_flag_2:
            print("\n\t\t[#]#[#] Golden content seems correct!")
            break

    # Faulty outputs
    for i in range(0,int(injection_num)):
        if i not in aborted_l:
            faulty_res_filename = f"./faulty_bitstreams/uB_results/uB_result_{i}.dat"
            done_flag_1 = False
            done_flag_2 = False
            timeout_flag = False
            faulty_content = open(faulty_res_filename,"r+")
            for line in faulty_content.read().splitlines():
                splitted_line = line.split()
                if (not done_flag_1) and ("DONE_1" in splitted_line):
                    done_flag_1 = True
                if (not done_flag_2) and ("DONE_2" in splitted_line):
                    done_flag_2 = True
                if done_flag_1 and done_flag_2:
                    print(f"\t\t[#]#[#] exec#{i} -> OK")
                    break
                
                # Example of exception signature: "---- Exception: XEXC_ID_FSL ----"
                if "Exception:" in splitted_line:
                    exc_text = splitted_line[2]
                    if exc_text not in exceptions_dict.keys():
                        exceptions_dict[exc_text] = 0
                    exceptions_dict[exc_text] += 1
                    print(f"\t\t[#]#[#] exec#{i} -> EXCEPTION")
                    exception_cnt+=1
                    exception_process_l.append(int(i))
                    break

            if (not done_flag_1) or (not done_flag_2):
                print(f"\t\t[#]#[#] exec#{i} -> HANG")
                hang_process_cnt+=1
                hang_process_l.append(int(i))
                dump_strange_output(faulty_res_filename, i, r_seed)
                continue


    # ******* Printing the results *******
    out_file = open(report_filepath,"a+")
    out_file.write(f"\t--FUNCTIONAL_ANALYSIS--")
    out_file.write(f"\nperformed_injections= {injection_num-aborted_cnt}")    
    out_file.write(f"\n\t[aborted_injections= {aborted_cnt}]")
    out_file.write(f"\ncorrect_results= {injection_num -aborted_cnt -faulty_cnt -hang_process_cnt -exception_cnt}")    
    out_file.write(f"\nfaulty_results= {faulty_cnt}")
    out_file.write(f"\nfaulty_results_bitstreams= {faulty_l}")    
    out_file.write(f"\nhang_processes= {hang_process_cnt}")
    out_file.write(f"\nhang_processes_bitstreams= {hang_process_l}")
    out_file.write(f"\nexceptions= {exception_cnt}")
    for exc_text in exceptions_dict.keys():
        out_file.write(f"\nException[ {exc_text} ]= {exceptions_dict[exc_text]}")

    out_file.close()

def dump_strange_output(strange_output_filename, inj_num, seed):
    strange_results_folder = "./fi_reports/strange_uB_results/"
    print(f"\nfile to be dumped is: {strange_output_filename} and will be copied as {strange_results_folder}s{seed}_#{inj_num}.dat")
    if  not path.exists(strange_results_folder):
        os.mkdir(strange_results_folder)
        print("\tCreated ./faulty_bitstreams/ !")

    original = strange_output_filename.replace('/', '\\')
    new = f"{strange_results_folder}s{seed}_#{inj_num}.dat".replace('/', '\\')
    os.system(fr'copy "{original}" "{new}"')