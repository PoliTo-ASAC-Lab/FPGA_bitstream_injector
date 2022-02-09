# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 16:06:35 2019

@author: Corrado
@modified_by: Daniele
"""
import serial
import time
from threading import Thread
import logging

class Listener:

    def __init__(self, port, baudrate,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                 serial_read_timeout=1, stop_keyword='', wait_application_for=5, wait_on_start=False, listener_time = None):

        self.logger = logging.getLogger(f'Listener_{hex(id(self))}')

        self.connection = None

        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.serial_read_timeout = serial_read_timeout
        self.buffer = ''
        self.stop_keyword = stop_keyword
        self.application_timeout = wait_application_for
        self.wait_on_start = wait_on_start
        self.listener_time = listener_time
        self.listener_state = None
        self.async_listener_thread = None

        return

    def connect(self):
        try:
            self.connection = serial.Serial(port=self.port,
                                            baudrate=self.baudrate,
                                            parity=self.parity,
                                            stopbits=self.stopbits,
                                            bytesize=self.bytesize,
                                            timeout=self.serial_read_timeout)
        except serial.SerialException as SE:
            self.logger.error(str(SE))
            raise SE
        return

    def close(self):
        self.connection.close()
        #print("closed_listener")
        return

    def do_async_listen(self, output_file):
        self.run_async_listener(output_file)
        return

    def do_listen(self, fp_outfile, listen_time = None, debug = True):
        self.clear_buffer()
        self.reset_state()

        if self.wait_on_start:
            tmp_byte_buffer = self.connection.read(64)
            while not tmp_byte_buffer:
                self.logger.info("LISTENER: nothing on serial... ")
                time.sleep(0.5)
                tmp_byte_buffer = self.connection.read(64)

            tmp_decoded_buffer = tmp_byte_buffer.decode("utf-8")

            self.logger.debug(tmp_decoded_buffer)
            if debug: print(f"LISTENER says\"{tmp_decoded_buffer}\"", end='')
            self.buffer += tmp_decoded_buffer
            fp_outfile.write(tmp_byte_buffer)

            self.clear_buffer(keep_keyword_window_chars=True)

        tic = time.time()
        initial_tic = time.time()

        completion_keywords = {
            "DONE_1": False,
            "DONE_2": False
        }
        completion_mark = False;

        while 1:
            completion_mark = True
            for keyword in completion_keywords.keys():
                if keyword in self.buffer:
                    completion_keywords[keyword] = True
            
            for keyword in completion_keywords.keys():
                completion_mark &= completion_keywords[keyword]

            if completion_mark == True:
                self.listener_state = 'completed'
                break

            if "Exception" in self.buffer:
                self.listener_state = 'exception'
                break

            print(time.time() - tic)
            if time.time() - tic > self.application_timeout:
                self.listener_state = 'application_timeout'
                break

            if listen_time is not None and time.time() - initial_tic > listen_time:
                self.listener_state = 'listened_enough'
                break


            tmp_byte_buffer = self.connection.read(32)
            if tmp_byte_buffer:
                tmp_decoded_buffer = tmp_byte_buffer.decode("utf-8",errors="replace")
                self.buffer += tmp_decoded_buffer
                fp_outfile.write(tmp_byte_buffer)
                self.logger.debug(tmp_decoded_buffer)
                if debug: print(f"LISTENER says\"{tmp_decoded_buffer}\"", end='')
                #self.clear_buffer(keep_keyword_window_chars=False)
                tic = time.time()

        self.clear_buffer()
        #print('', flush=True)

        fp_outfile.flush()
        time.sleep(10e-6)
        fp_outfile.write(self.listener_state.encode('utf-8'))
        self.logger.debug(self.listener_state)
        print(self.listener_state, end='')
        return self.listener_state

    def clear_buffer(self, keep_keyword_window_chars=False):
        # TODO: che schifo trova soluzione migliore (per mantenere limited buffer size)
        if not keep_keyword_window_chars:
            self.buffer = ''
        else:
            if len(self.buffer) > len(self.stop_keyword):
                self.buffer = self.buffer[-len(self.stop_keyword):]
        return

    def reset_state(self):
        self.state = None

    ##########################
    # thread control methods #
    ##########################
    def run_async_listener(self, logfile):
        assert self.async_listener_thread is None or not self.async_listener_thread.is_alive()

        self.async_listener_thread = self.AsyncListenerThread(self, logfile)
        self.async_listener_thread.start()
        return

    ###########
    # threads #
    ###########

    class AsyncListenerThread(Thread):
        def __init__(self, listener, logfile):
            Thread.__init__(self)

            self.listener = listener
            self.logfile = logfile
            self.logfile_fp = open(logfile, 'wb')

            return

        def run(self):
            self.listener.do_listen(self.logfile_fp, listen_time=self.listener.listener_time)
            self.logfile_fp.close()
            self.listener.logger.info(f'Listener Thread {self.ident} terminating  with State: {self.listener.listener_state}')

            return
