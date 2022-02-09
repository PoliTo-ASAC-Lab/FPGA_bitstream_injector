#!/usr/bin/env python3

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
import threading

from fi_lib.bitman import bitflip
from fi_lib.crc32 import CRC32_hash
from fi_lib.fi_utils import *
from fi_lib.report_zipper import report_zipper, report_zipper_FreeRTOS
from fi_lib.listener import Listener

# Random Seed setting
r_seed = int(time.time())

def XSCTmotivator(XSCTp, debug = True):
    # see (https://github.com/raczben/wexpect/issues/53)
    while(1):
        time.sleep(1)
        if debug: print("@#@#@pinging")
        XSCTcommunicate(XSCTproc, 'puts \"AO sto bene\"')

def getXSCT_pid(XSCTp, debug = True):
    XSCTp.sendline('puts [pid] ; join [concat "XSCT_" "DONE"] ""')
    XSCTp.expect('XSCT_DONE')
    pid = (int)((XSCTp.before).splitlines()[-1])
    if debug: print(pid)
    return pid

if __name__ == '__main__':

    ### Clearing the folders
    clear_folders()

    ### Setting Parameters
    
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    bitstream_file = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/ub_DDR_mem_wrapper.bit"
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####

    ELF_file = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/Testbed_02_app.elf"
    HW_file = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/cnstr_ub_DDR_mem_wrapper.xsa"
    faulty_bits_BASE_DIR = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/faulty_bitstreams"
    injection_num = 1
    
    if (
        not path.exists(bitstream_file)
        or not path.exists(ELF_file)
        or not path.exists(HW_file)
        or not path.exists(faulty_bits_BASE_DIR)
        ):
        exit("\tERROR: Check file(s) or dir(s) path(s)!")

    begin_time = datetime.datetime.now() ############################################################# TIMING_1_START

    ### Spawning the XSCT process and its motivator
    XSCTproc = wexpect.spawn('xsct') # to be pinged once every second
    XSCTproc_pid = getXSCT_pid(XSCTproc)

    XSCTcommunicate(XSCTproc, 'connect -url tcp:127.0.0.1:3121; puts "XSCT_DONE"') # connecting to local XSCT server
    # motivator pings every second the XSCT process to avoid performance issue (https://github.com/raczben/wexpect/issues/53)
    #XSCTmotivator_thread = threading.Thread(target= XSCTmotivator, args=(XSCTproc,), daemon=True) # daemon=True --> thread is killed when main finishes
    #XSCTmotivator_thread.start()

    ### Injecting bitstream
    bitflip_injection(bitstream_file,injection_num)

    #### Launching with golden bitstream
    app_listener = Listener('COM4', 9600, wait_application_for=8, listener_time=None)
    app_listener.connect()
    print(f"INFO_Injection#GOLDEN Opened Serial on COM5")

    # Programming FPGA and launching on hardware
    app_out_golden = "./faulty_bitstreams/uB_results/golden_uB_result.dat"
    FPGA_prog_and_exec(XSCTproc, app_listener, bitstream_file, HW_file, ELF_file, app_out_golden)

    # Closing serial connection
    #app_listener.close()

    golden_time = datetime.datetime.now() - begin_time ################################################ TIMING_1_END
    print(f"\nINFO_Injection#GOLDEN Closed Serial on COM5 - Elapsed time: {golden_time}")

    ### Launching with corrupted bitstream
    aborted_l = []
    aborted_cnt = 0

    # Opening serial connection
    #app_listener = Listener('COM4', 9600, wait_application_for=10, listener_time=None)
    #app_listener.connect()
    
    for i in range(injection_num): #for each injection
        faulty_bitstream = f"{faulty_bits_BASE_DIR}/inj_{i}.bit"
        begin_time = datetime.datetime.now() ############################################################# TIMING_1_START

        print(f"INFO_Injection#{i}: START")

        # Programming FPGA and launching on hardware
        print(f"INFO_Injection#{i}: Launching on FPGA\n\n")
        app_out_faulty = f"./faulty_bitstreams/uB_results/uB_result_{i}.dat"
        if not FPGA_prog_and_exec(XSCTproc, app_listener, bitstream_file, HW_file, ELF_file, app_out_faulty):
            print(F"ABORTED INJECTION #{i}")
            #XSCTproc.sendline("rst -processor")
            #XSCTproc.sendline("rst -system")
            aborted_l.append(i)
            aborted_cnt+=1

        # Closing serial connection
        injection_time = datetime.datetime.now() - begin_time ################################################ TIMING_1_END
        print(f"\nINFO_Injection#{i}: Closed Serial on COM4 - Elapsed time : {injection_time}")

    app_listener.close()

    ### Functional Analysis
    timestamp = (datetime.datetime.now()).strftime("%Y-%m-%d@%H%M")
    
    ## Baremetal (no exceptions)
    #functional_analysis(injection_num, f"./fi_reports/FI_campaign_{timestamp}_{injection_num}_s{r_seed}.txt")
    #report_zipper()

    ## FreeRTOS (exception handled)
    functional_analysis_FreeRTOS(injection_num, f"./fi_reports/FI_campaign_{timestamp}_{injection_num}_s{r_seed}.txt", aborted_l)
    report_zipper_FreeRTOS()

    ##############################################
    #TODO TROVARE UN MODO PER UCCIDERE IL PROCESSO DI XSCT
    ##############################################
    os.kill(XSCTproc_pid,signal.SIGTERM)
    XSCTproc.close()
