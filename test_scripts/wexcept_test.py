import wexpect
import sys
from fi_lib.listener import Listener

def XSCTcommunicate(child, command, debug=False):
    xsct_prompt = ['xsct%', 'Invalid', 'invalid', 'no targets', 'wrong', 'No ', 'no ', 'failed', 'unable', 'cannot', 'error']
    child.sendline(command)
    if child.expect(xsct_prompt) != 0: #an error occurred
        print(f"Error occurred in XSCT while trying to execute:\n\t{command}")
    if debug: 
    	print(child.before)

#child = wexpect.spawn('xsct')#, logfile = 'C:/Users/Daniele_LAB7/Desktop/log.txt', echo= True)
#child.expect('xsct%')
#XSCTcommunicate(child,'connect -url tcp:1frfrr27.0.0.1:3121', True)
#
#exit()

DEBUG_listener = False

listener = Listener('COM4', 9600, wait_application_for=2, listener_time=None)
listener.connect()

bitstream_file = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/ub_DDR_mem_wrapper.bit"
ELF_file = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/Testbed_02_app.elf"
HW_file = "C:/Users/Daniele_LAB7/Documents/GitHub/FPGA_bitstream_injector/cnstr_ub_DDR_mem_wrapper.xsa"
app_out_file = './faulty_bitstreams/uB_results/golden_uB_result.dat'

child = wexpect.spawn('xsct')
XSCTcommunicate(child, 'connect -url tcp:127.0.0.1:3121')
XSCTcommunicate(child, 'targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" }')
XSCTcommunicate(child, f'fpga -file {bitstream_file} -no-revision-check -skip-compatibility-check')
XSCTcommunicate(child, f'loadhw -hw {HW_file}')
XSCTcommunicate(child, 'rst -system')
XSCTcommunicate(child, f'dow {ELF_file}')

listener.do_async_listen(app_out_file)

XSCTcommunicate(child,'con ')

listener.async_listener_thread.join()

XSCTcommunicate(child, 'stop ')
XSCTcommunicate(child, 'rst -system')
child.close()

