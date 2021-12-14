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

    for i in range(0, int(injection_num)):

        # Selective Injection Coordinates
        coordinates_are_good = False
        while (coordinates_are_good == False):
            coordinates_are_good = True
            random_frame = random.randint(0,total_frames)
            random_byte = random.randint(0,words_per_frame*bytes_per_word)
            random_word = random_byte/32
            x_cord = start_byte + (starting_frame + random_frame) * words_per_frame * bytes_per_word
            y_cord = random_byte

            # negative constraints set 1
            if((random_frame > 637 and random_frame < 5266) and (random_word > 0 and random_word < 60)):
                coordinates_are_good = False            

            # negative constraints set 2
            if(random_frame > 1266 and random_frame < 5266):
                coordinates_are_good = False            

            # negative constraints set 3
            if((random_frame > 6484 and random_frame < 10474)):
                coordinates_are_good = False            
            
            # negative constraints set 4
            if(random_frame > 11715):
                coordinates_are_good = False
            
            # negative constraints set 5
            # negative constraints set 6
            # negative constraints set 7
        
        #print(f"DEBUG.:|Injection#{i}: x={random_frame}th frame, y={random_byte}th word ")



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