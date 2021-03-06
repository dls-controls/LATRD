"""
Created on 20 May 2016

@author: Alan Greer
"""
from __future__ import print_function

import argparse
import logging
import time
from latrd_channel import LATRDChannel
from latrd_message import LATRDMessageException, LATRDMessage, GetMessage, PutMessage, PostMessage, ResponseMessage
from latrd_reactor import LATRDReactor


class LATRDControlSimulator(object):
    DETECTOR_1M  = 1
    DETECTOR_10M = 10

    def __init__(self, type=DETECTOR_1M):
        logging.basicConfig(format='%(asctime)-15s %(message)s')
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._log.setLevel(logging.DEBUG)
        self._ctrl_channel = None
        self._type = type
        self._reactor = LATRDReactor()
        self._store = {
            "status":
                {
                    "detector":
                        {
                            "state": "Idle",
                            "description": "TRISTAN control interface",
                            "serial_number": "0",
                            "software_version": "0.0.1",
                            "sensor_material": "Silicon",
                            "sensor_thickness": "300 um",
                            "x_pixel_size": "55 um",
                            "y_pixel_size": "55 um",
                            "x_pixels_in_detector": 2048,
                            "y_pixels_in_detector": 512,
                            "timeslice_number": 4
                        },
                    "housekeeping":
                        {
                            "standby": "On",
                            "fem_power_enabled": [True] * self._type,
                            "psu_temp": [28.6] * self._type,
                            "psu_temp_alert": [False] * self._type,
                            "fan_alert": [False] * self._type,
                            "output_alert": [False] * self._type,
                            "current_sense": [1.5] * self._type,
                            "voltage_sense": [2.1] * self._type,
                            "remote_temp": [30.1] * self._type,
                            "fan_control_temp": [36.3] * self._type,
                            "tacho": [0.8] * self._type,
                            "pwm": [128] * self._type
                        },
                    "clock":
                        {
                            "dpll_lol": [True] * self._type,
                            "dpll_hold": [True] * self._type,
                            "clock_freq": [65.7] * self._type
                        },
                    "sensor":
                        {
                            "temp": [65.8] * self._type,
                            "humidity": [47.8] * self._type
                        },
                    "fem":
                        {
                            "temp": [45.3] * self._type
                        }
                },
            "config":
                {
                    "state": "Idle",
                    "exposure_time": 0.0,
                    "gap": 0.0,
                    "repeat_interval": 0.0,
                    "frames": 0,
                    "frames_per_trigger": 0,
                    "n_trigger": 0,
                    "mode": "Time_Energy",
                    "profile": "Standard",
                    "threshold": 5.2,
                    "timeslice":
                        {
                            "duration_rollover_bits": 18
                        },
                    "bias":
                        {
                            "voltage": 0.0,
                            "enable": False
                        },
                    "time": "2018-09-26T09:30Z"
                }
        }

    def setup_control_channel(self, endpoint):
        self._ctrl_channel = LATRDChannel(LATRDChannel.CHANNEL_TYPE_ROUTER)
        self._ctrl_channel.bind(endpoint)
        self._reactor.register_channel(self._ctrl_channel, self.handle_ctrl_msg)

    def start_reactor(self):
        self._log.debug("Starting reactor...")
        self._reactor.run()

    def handle_ctrl_msg(self):
        id = self._ctrl_channel.recv()
        msg = LATRDMessage.parse_json(self._ctrl_channel.recv())

        self._log.debug("Received message ID[%s]: %s", id, msg)
        if isinstance(msg, GetMessage):
            self._log.debug("Received GetMessage, parsing...")
            self.parse_get_msg(msg, id)
        elif isinstance(msg, PutMessage):
            self._log.debug("Received PutMessage, parsing...")
            self.parse_put_msg(msg)
        elif isinstance(msg, PostMessage):
            self._log.debug("Received PostMessage, parsing...")
            self.parse_post_msg(msg)
        else:
            raise LATRDMessageException("Unknown message type received")

    def parse_get_msg(self, msg, send_id):
        # Check the parameter keys and retrieve the values from the store
        values = {}
        self.read_parameters(self._store, msg.params, values)
        self._log.debug("Return value object: %s", values)
        reply = ResponseMessage(msg.msg_id, values, ResponseMessage.RESPONSE_OK)
        self._ctrl_channel.send_multi([send_id, reply])

    def parse_put_msg(self, msg):
        # Retrieve the parameters and merge them with the store
        params = msg.params
        for key in params:
            self.apply_parameters(self._store, key, params[key])
        self._log.debug("Updated parameter Store: %s", self._store)
        reply = ResponseMessage(msg.msg_id)
        self._ctrl_channel.send(reply)

    def parse_post_msg(self, msg):
        # Nothing to do here, just wait two seconds before replying
        time.sleep(2.0)
        # Check for the "Run" command.  If it is sent and the simulated script has been supplied then execute it

        reply = ResponseMessage(msg.msg_id)
        self._ctrl_channel.send(reply)

    def apply_parameters(self, store, key, param):
        if key not in store:
            store[key] = param
        else:
            if isinstance(param, dict):
                for new_key in param:
                    self.apply_parameters(store[key], new_key, param[new_key])
            else:
                store[key] = param

    def read_parameters(self, store, param, values):
        self._log.debug("Params: %s", param)
        for key in param:
            if isinstance(param[key], dict):
                values[key] = {}
                self.read_parameters(store[key], param[key], values[key])
            else:
                values[key] = store[key]


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--control", default="tcp://127.0.0.1:7001", help="Control endpoint")
    args = parser.parse_args()
    return args


def main():
    args = options()

    simulator = LATRDControlSimulator()
    simulator.setup_control_channel(args.control)
    simulator.start_reactor()


if __name__ == '__main__':
    main()

