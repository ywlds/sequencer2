#!/usr/bin/env python
# -*- mode: Python; coding: latin-1 -*-
# Time-stamp: "2008-07-01 13:28:51 c704271"

#  file       test_lvds_bus.py
#  copyright  (c) Philipp Schindler 2008
#  url        http://pulse-sequencer.sf.net

import logging
from sequencer2 import sequencer
from sequencer2 import api
from sequencer2 import comm
from sequencer2 import ad9910
from sequencer2 import ptplog

class HardwareTests:
    """Hardware tests for the DDS board"""
    def __init__(self, nonet=False):
        self.nonet = nonet
        self.logger = ptplog.ptplog(level=logging.DEBUG)

    def test_lvds_bus_single(self):
        "Test the LVDS bus. Use this with the corresponding signal tap file"
        my_sequencer = sequencer.sequencer()
        my_api = api.api(my_sequencer)
        my_api.ttl_value(0xffff, 0)
        my_api.ttl_value(0xffff, 1)
        my_api.ttl_value(0xaaaa, 0)
        my_api.ttl_value(0xaaaa, 1)
        my_api.wait(100)
        self.compile(my_sequencer)

    def test_lvds_bus_infinite(self):
        "Test the LVDS bus. Use this with the corresponding signal tap file"
        my_sequencer = sequencer.sequencer()
        my_api = api.api(my_sequencer)
        my_api.label("start_loop")
        my_api.ttl_value(0xffff, 0)
        my_api.ttl_value(0xffff, 1)
        my_api.ttl_value(0xaaaa, 0)
        my_api.ttl_value(0xaaaa, 1)
        my_api.wait(100)
        my_api.jump("start_loop")
        self.compile(my_sequencer)

    def test_dds_simple(self, frequency=10):
        "Just sets a single profile of the dds and activates it"
        my_sequencer = sequencer.sequencer()
        my_api = api.api(my_sequencer)
        dds_device = ad9910.AD9910(0, 800)
        my_api.init_dds(dds_device)
        my_api.set_dds_freq(dds_device, frequency, 0)
        my_api.update_dds(dds_device)
        my_api.dac_value(0, 2**14-100)
        self.compile(my_sequencer)

    def compile(self, my_sequencer):
        "compile and send the sequence"
        my_sequencer.compile_sequence()
        ptp1 = comm.PTPComm(self.nonet)
        ptp1.send_code(my_sequencer.word_list)

# test_lvds_bus.py ends here
