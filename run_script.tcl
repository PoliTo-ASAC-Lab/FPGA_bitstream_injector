#### usage: xsct.bat run_script.tcl [bitstream_file] [ELF_file] [i]

#### WARNING! Use '/' instead of '\' when passing this file as script to xsct.bat
connect -url tcp:127.0.0.1:3121
#targets -set -filter {jtag_cable_name =~ "Digilent JTAG-SMT2NC 210308AAFF0C" && level==0} -index 0
#fpga -skip-compatibility-check -no-revision-check -file [lindex $argv 0]
#fpga -skip-compatibility-check -no-revision-check -file [lindex $argv 0]

after 500

if { [catch {fpga -file [lindex $argv 0]}] } {
    puts "EXEC_INFO: Injection Aborted!"
    set aborted [open ./faulty_bitstreams/uB_results/aborted.txt a+] 
    set str [lindex $argv 2]
    puts $aborted $str
    exit
}


targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
rst -system

if { [catch {dow [lindex $argv 1]}] } {
    puts "EXEC_INFO: Injection Aborted!"
    set aborted [open ./faulty_bitstreams/uB_results/aborted.txt a+] 
    set str [lindex $argv 2]
    puts $aborted $str
    exit
}

bpadd -addr &exit
puts "EXEC_INFO: Executing ELF..."

#con -block 
#con -block -timeout 10 
if { [catch {con -block -timeout 10}] } {
    puts "EXEC_INFO: MicroBlaze halted!"
    set hang_processes [open ./faulty_bitstreams/uB_results/hang_processes.txt a+] 
    set str [lindex $argv 2]
    puts $hang_processes $str
    exit
} else {
    puts "EXEC_INFO: Execution ended...Exiting"
#    set complete_processes [open ./faulty_bitstreams/uB_results/complete_processes.txt a+] 
#    set str [lindex $argv 2]
#    puts $complete_processes $str
    exit
}