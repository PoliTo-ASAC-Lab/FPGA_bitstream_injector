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

from fi_lib.bitman import bitflip
from fi_lib.crc32 import CRC32_hash
from fi_lib.fi_utils import *
from fi_lib.report_zipper import report_zipper

# Random Seed setting
r_seed = int(time.time())

if __name__ == '__main__':

    ### Clearing the folders
    clear_folders()
    ### Setting Parameters
    bitstream_file = "C:/Users/Daniele_LAB7/Desktop/FPGA_fault_injection/run/ub_base_wrapper_plain_new.bit"
    
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####
    ##### REMEMBER TO GENERATE BITSTREAM DISABLING CRC WORD #####

    ELF_file = "C:/Users/Daniele_LAB7/Desktop/FPGA_fault_injection/run/EFR_testbed_01_Aurora_Int_sw.elf"
    
    injection_num = 200
    if not path.exists(bitstream_file) or not path.exists(ELF_file):
        exit("\tERROR: Check file(s) path(s)!")

    
    ### Injecting bitstream
    bitflip_injection(bitstream_file,injection_num)

    ### Launching with golden bitstream
    # Opening serial connection
    command = f"plink -serial com3"
    command_l = shlex.split(command)
    print(command_l)
    serial_connection = subprocess.Popen(command_l, stdout=open(f"./faulty_bitstreams/uB_results/golden_uB_result.dat","w"))
    print(f"INFO_Injection#GOLDEN Opened Serial on COM5")

    # Programming FPGA and launching on hardware
    print(f"INFO_Injection#GOLDEN: Launching on FPGA\n\n")
    command = f"C:/Xilinx/Vitis/2021.1/bin/xsct.bat ./run_script.tcl {bitstream_file} {ELF_file}"
    command_l = shlex.split(command)
    launch_on_FPGA = subprocess.run(command_l)#, stdout=open("out_log.txt","w"))

    # Closing serial connection
    subprocess.call(['taskkill', '/F', '/T', '/PID', str(serial_connection.pid)])
    print(f"\nINFO_Injection#GOLDEN Closed Serial on COM5")


    ### Launching with corrupted bitstream
    for i in range(injection_num): #for each injection
        faulty_bitstream = f"C:/Users/Daniele_LAB7/Desktop/FPGA_fault_injection/run/faulty_bitstreams/inj_{i}.bit"

        # Opening serial connection
        command = f"plink -serial com3"
        command_l = shlex.split(command)
        serial_connection = subprocess.Popen(command_l, stdout=open(f"./faulty_bitstreams/uB_results/uB_result_{i}.dat","w"))
        print(f"INFO_Injection#{i}: Opened Serial on COM5")

        # Programming FPGA and launching on hardware
        print(f"INFO_Injection#{i}: Launching on FPGA\n\n")
        command = f"C:/Xilinx/Vitis/2021.1/bin/xsct.bat ./run_script.tcl {faulty_bitstream} {ELF_file} {i}"
        command_l = shlex.split(command)
        launch_on_FPGA = subprocess.run(command_l)#, stdout=open("out_log.txt","w"))

    #    #print(f"exit code is {process_exit_code}")
    #    if process_exit_code == None:
    #        print("terminating")
    #        os.kill(proc.pid, signal.CTRL_C_EVENT)
    #        os.kill(proc.pid, signal.CTRL_C_EVENT) #to be sure

        # Closing serial connection
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(serial_connection.pid)]) # See: http://mackeblog.blogspot.com/2012/05/killing-subprocesses-on-windows-in.html
        print(f"\nINFO_Injection#{i}: Closed Serial on COM5")

    ### Functional Analysis
    timestamp = (datetime.datetime.now()).strftime("%Y-%m-%d@%H%M")
    functional_analysis(injection_num, f"./fi_reports/FI_campaign_{timestamp}_{injection_num}_s{r_seed}.txt")
    report_zipper()