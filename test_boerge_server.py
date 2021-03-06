#!/usr/bin/env python
# -*- mode: Python; coding: latin-1 -*-
# Time-stamp: "2009-07-20 12:19:04 c704271"

#  file       test_ipython.py
#  copyright  (c) Philipp Schindler 2008
#  url        http://pulse-sequencer.sf.net test

from server import main_program
from sequencer2 import ptplog
import logging

log_dict = {"api" : logging.INFO ,
            "sequencer2" : logging.ERROR,
            "" : logging.ERROR}
logger=ptplog.ptplog()

logger=ptplog.ptplog(level=logging.DEBUG)


cmd_str = "NAME,PMTreadout.py;CYCLES,1;TRIGGER,NONE;INIT_FREQ,CYCLE;FLOAT,det_time,30.000000;FLOAT,freq729,486.000000;FLOAT,power729,0.000000;FLOAT,gl_cam_time,2000.000000;BOOL,switch729,0;TRANSITION,carrier;RABI,1:1.000000;SLOPE_TYPE,blackman;SLOPE_DUR,0.000000;AMPL,-15.00000;FREQ,10.0;IONS,1:0.000000,2:0.000000,3:0.000000;SWEEP,0.000000;PORT,1;TRANSITION,clock1;RABI,1:1.000000;SLOPE_TYPE,blackman;SLOPE_DUR,0.000000;AMPL,-15.000000;FREQ,0.0;IONS,1:0.000000,2:0.000000,3:0.000000;SWEEP,0.000000;PORT,1;TRANSITION,clock2;RABI,1:6.500000,2:6.500000;SLOPE_TYPE,blackman;SLOPE_DUR,0.000000;AMPL,-15.000000;FREQ,1.0;IONS,1:0.000000,2:0.000000,3:0.000000;SWEEP,0.000000;PORT,1;TTLWORD,0;TTLMASK,0"

print("########################################################\n")
print("test boerge server \n Generating fake command string \n  ")
print(cmd_str)
print("\n########################################################\n")


# cmd_str = generate_cmd_str("test_bichro_sequence.py", nr_of_car=5)

my_main_program = main_program.MainProgram()
return_var = my_main_program.execute_program(cmd_str)

#log1 = logging.getLogger()
#handler = log1.handlers[1]
#handler.target.doRollover()
#handler.flush()


#if return_var.is_error:
#    self.fail(return_var.return_string)

