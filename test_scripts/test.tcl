connect -url tcp:127.0.0.1:3121
set bitstream_file C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/ub_DDR_mem_wrapper.bit
set ELF_file C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/Testbed_02_app.elf
for {set i 0} {$i < 10} {incr i} {
	after 3000
	set ping [clock seconds]
	targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }
	fpga -file $bitstream_file -no-revision-check -skip-compatibility-check
	while { [catch {dow $ELF_file}] } {rst -system}
	catch {con -block -timeout 1}
	rst -processor
	set pong [clock seconds]
	puts [expr {$pong - $ping}]
	puts "FINISHED $i"
}