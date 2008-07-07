#!/usr/bin/env python
# -*- mode: Python; coding: latin-1 -*-
# Time-stamp: "04-Jul-2008 20:27:49 viellieb"

#  file       instruction_handler.py
#  copyright  (c) Philipp Schindler 2008
#  url        http://pulse-sequencer.sf.net


"""Defines the high level instructions which are used by
functions in user_fucntion.py"""

from transitions import Transitions
from  sequencer2 import config

import logging

global_config = config.Config()
global_reference_frequency = global_config.get_float("SERVER","reference_frequency")
global_clk_divider = global_config.get_float("SERVER","clk_divider")

global_config.get_all_dict("Durations")
global_get_duration = global_config.get_float_dict_val

class SeqInstruction:
    "Base class used for all intructions"
    duration = 0.0
    start_time = 0.0
    cycle_time = 1 / global_reference_frequency * global_clk_divider
    get_hardware_duration = global_get_duration
    is_last = False
    is_added = False
    sequence_var = []
    name = "generic Instruction"

    def add_insn(self, sequence_var):
        "Adds the instructions to the sequence dictionary"
        if self.is_added:
            raise RuntimeError("Instruction can not be added twice")
        sequence_var.append(self)
        self.is_added = True
        return sequence_var

    def get_duration(self):
        "returns the duration of the instruction"
        return self.duration

    def __str__(self):
        return str(self.name) + " | start: " + str(self.start_time) \
            + " | dur: " + str(self.duration) + " | last: " + str(self.is_last)

    def resolve_conflict(self, other_item):
        "By default no conflict is resolved"
        return False

class TTLPulse(SeqInstruction):
    "generates a TTL pulse"
    def __init__(self, start_time, duration, device_key, is_last=True):
        stop_time = start_time + duration
        value_on = []
        value_off = []

        if str(device_key) == device_key:
            device_key = [device_key]

        for item in device_key:
            value_on.append(1)
            value_off.append(0)

        self.start_time = start_time
        self.duration = duration
        self.name = "TTL_Pulse"
        self.is_last = is_last
        self.sequence_var = []

        start_event = TTLEvent(start_time, device_key, value_on, is_last=False)
        stop_event = TTLEvent(stop_time, device_key, value_off, is_last=is_last)

        self.sequence_var = start_event.add_insn(self.sequence_var)
        self.sequence_var = stop_event.add_insn(self.sequence_var)

class RFPulse(SeqInstruction):
    "Generates an RF pulse"
    def __init__(self, start_time, theta, phi, ion, transitions, \
                     is_last=False, address=0):
        # Missing: Modify DDSSwitch event to support different indeces for
        #    the dds and the phase register
        #
        #    Add a set_dds_freq event if the transition is not in the dds
        #    profile already
        #
        #    Modify duration if a set dds_freq event is needed
        #    BUG: The index_list should depend also on the DDS instance !!!

        self.logger = logging.getLogger("server")
        self.logger.debug("Switching frequency to: "+str(transitions))
#        current_dds_index = None
        try:
            transition_obj = transitions[transitions.current_transition]
        except KeyError:
            raise RuntimeError("Transition name not found: " + \
                                   str(transitions.current_transition))

#        for dds_index, trans  in transitions.index_list.iteritems():
#            if trans == transition_obj:
#                current_dds_index = dds_index

#        if current_dds_index == None:
#            raise RuntimeError("Transition not in DDS registers")
        try:
            pulse_duration = transition_obj.t_rabi[ion] * theta
        except KeyError:
            raise RuntimeError("Error while getting Rabi frequency for ion "+str(ion))

        amplitude = transition_obj.amplitude
        if transition_obj.slope_type != "None":
            slope_duration = transition_obj.slope_duration
        else:
            slope_duration = 0
        transition_name = transition_obj.name
        # Missing: global configuration
        cycle_time = self.cycle_time
        dac_switch_time = self.get_hardware_duration("dac_duration")
        dds_switch_time = self.get_hardware_duration("dds_duration")
        #Switch the DDS on before the DAC
        dds_start_time = start_time
        dac_start_time = start_time + dds_switch_time
        #Switch the DAC of berfore the DDS
        dac_stop_time = dds_start_time + pulse_duration - slope_duration
        dds_stop_time = dac_stop_time + dac_switch_time

        amplitude_off = 0

        #Let's check if we're using a shaped pulse or not ....
        if slope_duration < cycle_time :
            dac_start_event = DACEvent(dac_start_time, amplitude, \
                                            address, is_last=False)
            dac_stop_event = DACEvent(dac_start_time, amplitude_off, \
                                           address, is_last=False)
        else:
            dac_start_event = DACShapeEvent(dac_start_time, transition_obj, \
                                                  address, rising=True, is_last=False)
            dac_stop_event = DACShapeEvent(dac_stop_time, transition_obj, \
                                                 address, rising=False, is_last=False)

        dds_start_event = DDSSwitchEvent(dds_start_time, address, transition_name, \
                                                   phi,  is_last=False)
        #The DDS stop event switches to a zero frequency
        dds_stop_event = DDSSwitchEvent(dds_stop_time, address, "NULL", \
                                                   phi, is_last=is_last)
        # Add the events to the sequence
        self.sequence_var = dac_start_event.add_insn(self.sequence_var)
        self.sequence_var = dac_stop_event.add_insn(self.sequence_var)
        self.sequence_var = dds_start_event.add_insn(self.sequence_var)
        self.sequence_var = dds_stop_event.add_insn(self.sequence_var)


class RFBichroPulse(SeqInstruction):
    "Generates an RF pulse"
    def __init__(self, start_time, theta, phi, ion, transitions, \
                 is_last=False, address=0, address2=1):
        # Missing: Modify DDSSwitch event to support different indeces for
        #    the dds and the phase register
        #
        #    Add a set_dds_freq event if the transition is not in the dds
        #    profile already
        #
        #    Modify duration if a set dds_freq event is needed
        #    BUG: The index_list should depend also on the DDS instance !!!

        self.logger = logging.getLogger("server")
        self.logger.debug("Switching frequency to: "+str(transitions))
#        current_dds_index = None
        try:
            transition_obj = transitions[transitions.current_transition]
            transition_obj2 = transitions[transitions.transition2_name]
        except KeyError:
            raise RuntimeError("Bichro Pulse Transition name not found: " + \
                                   str(transitions.current_transition))

#        for dds_index, trans  in transitions.index_list.iteritems():
#            if trans == transition_obj:
#                current_dds_index = dds_index

#        if current_dds_index == None:
#            raise RuntimeError("Transition not in DDS registers")
        try:
            pulse_duration = transition_obj.t_rabi[ion] * theta
        except KeyError:
            raise RuntimeError("Error while getting Rabi frequency for ion "+str(ion))

        amplitude = transition_obj.amplitude
        if transition_obj.slope_type != "None":
            slope_duration = transition_obj.slope_duration
        else:
            slope_duration = 0
        transition_name = transition_obj.name
        transition2_name = transition_obj2.name
        # Missing: global configuration
        cycle_time = self.cycle_time
        dac_switch_time = self.get_hardware_duration("dac_duration")
        dds_switch_time = self.get_hardware_duration("dds_duration")
        #Switch the DDS on before the DAC
        dds_start_time = start_time
        dds_start_time2 = start_time + dds_switch_time
        dac_start_time = start_time + 2 * dds_switch_time
        #Switch the DAC of berfore the DDS
        dac_stop_time = dds_start_time + pulse_duration - slope_duration
        dds_stop_time = dac_stop_time + dac_switch_time
        dds_stop_time2 = dac_stop_time + dac_switch_time + dds_switch_time
        amplitude_off = 0

        #Let's check if we're using a shaped pulse or not ....
        if slope_duration < cycle_time :
            dac_start_event = DACEvent(dac_start_time, amplitude, \
                                            address, is_last=False)
            dac_stop_event = DACEvent(dac_start_time, amplitude_off, \
                                           address, is_last=False)
        else:
            dac_start_event = DACShapeEvent(dac_start_time, transition_obj, \
                                                  address, rising=True, is_last=False)
            dac_stop_event = DACShapeEvent(dac_stop_time, transition_obj, \
                                                 address, rising=False, is_last=False)

        dds_start_event = DDSSwitchEvent(dds_start_time, address, transition_name, \
                                                   phi,  is_last=False)
        dds_start_event2 = DDSSwitchEvent(dds_start_time2, address2, transition2_name, \
                                                   phi,  is_last=False)
        #The DDS stop event switches to a zero frequency
        dds_stop_event = DDSSwitchEvent(dds_stop_time, address, "NULL", \
                                        phi, is_last=False)
        dds_stop_event2 = DDSSwitchEvent(dds_stop_time2, address2, "NULL", \
                                         phi, is_last=is_last)
        # Add the events to the sequence
        self.sequence_var = dac_start_event.add_insn(self.sequence_var)
        self.sequence_var = dac_stop_event.add_insn(self.sequence_var)
        self.sequence_var = dds_start_event.add_insn(self.sequence_var)
        self.sequence_var = dds_stop_event.add_insn(self.sequence_var)
        self.sequence_var = dds_start_event2.add_insn(self.sequence_var)
        self.sequence_var = dds_stop_event2.add_insn(self.sequence_var)

class TTLEvent(SeqInstruction):
    "Generates a ttl high or low event"
    def __init__(self, start_time, device_key, value, is_last=True):
        self.val_dict = {}

        for index in range(len(device_key)):
            self.val_dict[device_key[index]] = value[index]
        self.start_time = start_time
        self.device_key = device_key
        self.name = "TTLEvent"
        self.duration = self.cycle_time
        self.is_last = is_last
        self.value = value

    def handle_instruction(self, api):
        api.ttl_set_multiple(self.val_dict)

    def resolve_conflict(self, other_item):
        "We can combine two TTL Events"
        if other_item.name != "TTLEvent":
            return None
        self.val_dict.update(other_item.val_dict)
        self.device_key += other_item.device_key
        return True

    def __str__(self):
        return str(self.name) + " start: " + str(self.start_time) \
            + " | dur: " + str(self.duration) + " | last: " + str(self.is_last) \
            + " | key: " +str(self.val_dict)


class DACEvent(SeqInstruction):
    "Generates a DAC event"
    def __init__(self, start_time, value, address, is_last=True):
        self.start_time = start_time
        self.name = "DACEvent"
        self.duration = self.cycle_time * 3.0
        self.is_last = is_last
        self.value = value
        self.address = address

    def handle_instruction(self, api):
        api.dac_value(self.address, self.value)

    def __str__(self):
        return str(self.name) + " start: " + str(self.start_time) \
            + " | dur: " + str(self.duration) + " | last: " + str(self.is_last) \
            + " | addr: "+str(self.address) + " | val: "+str(self.value)



class DACShapeEvent(SeqInstruction):
    "A simple shaped DAC pulse"
    def __init__(self, start_time, transition, dac_address, rising=True, is_last=False , step_nr=100):
        self.start_time = start_time
        self.name = "DAC_Shape_Event"
        self.slope_duration = float(transition.slope_duration)
        self.amplitude = transition.amplitude
        self.is_rising = rising
        self.is_last = is_last
        self.dac_address = dac_address
        # Get the transtion function
        transitions = Transitions()
        try:
            self.shape_func = transitions.trans_dict[transition.slope_type]
        except KeyError:
            raise RuntimeError("Error while getting slope function: "+str(transition.slope_type))
        self.duration = self.slope_duration
        self.step_nr = step_nr
        #calculate the waiting time in between two steps
        self.wait_time = self.slope_duration / float(self.step_nr) \
                         - self.get_hardware_duration("dac_duration") * self.cycle_time
        # Check if we need to decrease the step count
        if self.wait_time < 0:
            self.wait_time = 0
            self.step_nr = int(self.slope_duration / self.get_hardware_duration("dac_duration"))

    def handle_instruction(self, api):
        for i in range(self.step_nr):
            x = float(i)/float(self.step_nr)
            dac_value = self.shape_func(x, self.is_rising) + self.amplitude
            api.dac_value(self.dac_address, dac_value)
            if self.wait_time > 0:
                api.wait(self.wait_time)

    def __str__(self):
        return str(self.name) + " start: " + str(self.start_time) \
            + " | dur: " + str(self.duration) + " | last: " + str(self.is_last) \
            + " | dac_addr: "+str(self.dac_address) + " | ampl: " + str(self.amplitude) \
            + " | slope_dur: "+str(self.slope_duration)


class DDSSwitchEvent(SeqInstruction):
    "Generates a DDS freq switching event"
    def __init__(self, start_time, dds_address, index, phase=0, is_last=False):
        self.start_time = start_time
        self.index = index
        self.phase = phase
        self.is_last = is_last
        self.dds_address = dds_address
        self.name = "DDS_Switch_Event"

    def handle_instruction(self, api):
        try:
            if int(self.index) == self.index:
                real_index = self.index
        except:
            try:
                real_index = api.dds_profile_list[self.index]
            except:
                raise RuntimeError("Transition name not found: "+str(self.index))

        try:
            dds_instance = api.dds_list[self.dds_address]
        except IndexError:
            raise RuntimeError("No DDS known with address: "+str(self.dds_address))
        api.switch_frequency(dds_instance, real_index, self.phase)

    def __str__(self):
        return str(self.name) + " start: " + str(self.start_time) \
            + " | dur: " + str(self.duration) + " | last: " + str(self.is_last) \
            + " | dds_addr: "+str(self.dds_address) + " | index: "+str(self.index)

# instruction_handler.py ends here