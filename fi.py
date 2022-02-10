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
    faulty_bits_BASE_DIR = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/faulty_bitstreams"
    injection_num = 50
    
    if (
        not path.exists(bitstream_file)
        or not path.exists(ELF_file)
        or not path.exists(faulty_bits_BASE_DIR)
        ):
        exit("\tERROR: Check file(s) or dir(s) path(s)!")

    begin_time = datetime.datetime.now() ############################################################# TIMING_1_START

    ### Spawning the XSCT process and getting its PID
    XSCTproc = wexpect.spawn('xsct') # to be pinged once every second
    XSCTproc_pid = getXSCT_pid(XSCTproc)
    XSCTcommunicate(XSCTproc, 'connect -url tcp:127.0.0.1:3121; puts "XSCT_DONE"') # connecting to local XSCT server

    ### Injecting bitstream
    bitflip_injection(bitstream_file,injection_num)

    #### Launching with golden bitstream
    app_listener = Listener('COM4', 9600, wait_application_for=8, listener_time=None)
    app_listener.connect()
    print(f"INFO_Injection#GOLDEN: START")

    # Programming FPGA and launching on hardware
    app_out_golden = "./faulty_bitstreams/uB_results/golden_uB_result.dat"
    FPGA_prog_and_exec(XSCTproc, app_listener, bitstream_file, ELF_file, app_out_golden)

    golden_time = datetime.datetime.now() - begin_time ################################################ TIMING_1_END
    print(f"\nINFO_Injection#GOLDEN: END - Elapsed time: {golden_time}")

    ### Launching with corrupted bitstream
    aborted_l = []
    aborted_cnt = 0
    
    for i in range(injection_num): #for each injection
        faulty_bitstream = f"{faulty_bits_BASE_DIR}/inj_{i}.bit"
        begin_time = datetime.datetime.now() ############################################################# TIMING_2_START

        print(f"INFO_Injection#{i}: START")

        # Programming FPGA and launching on hardware
        print(f"INFO_Injection#{i}: Launching on FPGA\n\n")
        app_out_faulty = f"./faulty_bitstreams/uB_results/uB_result_{i}.dat"
        if not FPGA_prog_and_exec(XSCTproc, app_listener, faulty_bitstream, ELF_file, app_out_faulty):
            print(F"ABORTED INJECTION")
            for j in range(i,injection_num): aborted_l.append(i)
            break # terminating the injection campaign, the remaining injections would fail
            

        # Closing serial connection
        injection_time = datetime.datetime.now() - begin_time ################################################ TIMING_2_END
        print(f"\nINFO_Injection#{i}: END - Elapsed time : {injection_time}")

    app_listener.close()

    ### Functional Analysis
    timestamp = (datetime.datetime.now()).strftime("%Y-%m-%d@%H%M")
    
    ## A) Baremetal (no exceptions)
    #functional_analysis(injection_num, f"./fi_reports/FI_campaign_{timestamp}_{injection_num}_s{r_seed}.txt")
    #report_zipper()

    ## B) FreeRTOS (exception handled)
    functional_analysis_FreeRTOS(injection_num, f"./fi_reports/FI_campaign_{timestamp}_{injection_num}_s{r_seed}.txt", aborted_l, r_seed)
    report_zipper_FreeRTOS()

    ##############################################
    #TODO TROVARE UN MODO PER UCCIDERE IL PROCESSO DI XSCT
    ##############################################
    os.kill(XSCTproc_pid,signal.SIGTERM)
    XSCTproc.close()
