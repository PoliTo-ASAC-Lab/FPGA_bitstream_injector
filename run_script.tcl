#### usage: xsct.bat run_script.tcl [bitstream_file] [ELF_file] [i]

#### WARNING! Use '/' instead of '\' when passing this file as script to xsct.bat
connect -url tcp:127.0.0.1:3121
#targets -set -filter {jtag_cable_name =~ "Digilent JTAG-SMT2NC 210308AAFF0C" && level==0} -index 0
#fpga -skip-compatibility-check -no-revision-check -file [lindex $argv 0]
#fpga -skip-compatibility-check -no-revision-check -file [lindex $argv 0]

#after 100

# 1) Programming FPGA
targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
#if { [catch {fpga -file "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/ub_DDR_mem_wrapper.bit"}] } {
#fpga -file [lindex $argv 0] -no-revision-check -skip-compatibility-check
if { [catch {fpga -file [lindex $argv 0] -no-revision-check -skip-compatibility-check}] } {
    puts "EXEC_INFO: Injection Aborted while programming the FPGA!"
    set aborted [open ./faulty_bitstreams/uB_results/aborted.txt a+] 
    set str [lindex $argv 2]
    puts $aborted $str
    exit
}

# 2) Loading HW platform
targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
#loadhw -hw C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/cnstr_ub_DDR_mem_wrapper.xsa -regs
#if { [catch {loadhw -hw [lindex $argv 3] -regs}] } {
if { [catch {loadhw -hw [lindex $argv 3]}] } {
    puts "EXEC_INFO: Injection Aborted while loading HW file!"
    set aborted [open ./faulty_bitstreams/uB_results/aborted.txt a+] 
    set str [lindex $argv 2]
    puts $aborted $str
    exit
}

# 3) Reset the system
targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
rst -system

# 4) Downloading the application
targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
#if { [catch {dow "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/Testbed_02_app.elf" }]} {
if { [catch {dow [lindex $argv 1]}] } {
    puts "EXEC_INFO: Injection Aborted2!"
    set aborted [open ./faulty_bitstreams/uB_results/aborted.txt a+] 
    set str [lindex $argv 2]
    puts $aborted $str
    exit
}

# 5) Adding breakpoint to catch the end of execution
targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
bpadd -addr &exit
puts "EXEC_INFO: Executing ELF..."

# 6) Starting the execution
## 6.A) Letting execute until break point (WARNING: could never exit)
#targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
#con -block 
#puts "EXEC_INFO: Execution ended...Exiting"

## 6.B) Letting execute until breakpoint, or for 1 sec and then kill execution
targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
if { [catch {con -block -timeout 1}] } {
    puts "EXEC_INFO: Execution ended...Exiting"
    #stop
    #rst -system
    #rst -processor
}
exit

## 6.C) Letting execute until breakpoint or for 10 seconds, keeping track of hang processes  
#targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
#if { [catch {con -block -timeout 10}] } {
#    puts "EXEC_INFO: MicroBlaze halted!"
#    set hang_processes [open ./faulty_bitstreams/uB_results/hang_processes.txt a+] 
#    set str [lindex $argv 2]
#    puts $hang_processes $str
#    exit
#} else {
#    puts "EXEC_INFO: Execution ended...Exiting"
##    set complete_processes [open ./faulty_bitstreams/uB_results/complete_processes.txt a+] 
##    set str [lindex $argv 2]
##    puts $complete_processes $str
#    exit
#}