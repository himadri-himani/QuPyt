"""
This file handles all aspect of the various signal sources in
active use. Newly requested devices are opened and added
to dict of used devices, while no longer needed ones are close
and deleted.
Edge cases like no requested devices as well as values to be set
or sweeped are handled here as well.
"""
import copy
import logging
from typing import Dict, Any, Tuple
import numpy as np
from qupyt.hardware.signal_sources import WindFreak, WindFreakHDM
from qupyt.hardware.signal_sources import SignalSource, MockSignalSource


def close_superfluous_devices(devs: Dict[str, Any],
                              requested_devs: Dict[str, Any]) -> Dict[str, Any]:
    """close all devices not requested for the next measurement.
    Compare dict of requested and existing devices. Close and remove
    devices not requested."""
    requested_name_address_tuples = [
        (key, val["address"]) for key, val in requested_devs.items()
    ]
    for key, value in list(devs.items()):
        if (key, value["address"]) not in requested_name_address_tuples:
            devs[key]["device"].close()
            rem = devs.pop(key)
            logging.info("Removed {} from active devices dict".format(rem)
                         .ljust(65, '.') + '[done]')
    return devs


def open_new_requested_devices(devs: Dict[str, Any],
                               requested_devs: Dict[str, Any]) -> Dict[str, Any]:
    """Open all devices requested for the next measurement that are
    not in the current active dict. Compare dict of requested and
    existing devices."""
    current_name_address_tuples = [(key, val["address"])
                                   for key, val in devs.items()]
    for key, value in list(requested_devs.items()):
        if (key, value["address"]) not in current_name_address_tuples:
            if value["device_type"] == 'WindFreak':
                device = WindFreak(value['address'])
            elif value["device_type"] == 'WindFreakHDM':
                device = WindFreakHDM(value['address'])
            elif value["device_type"] == "Mock":
                device = MockSignalSource(value["address"])
            else:
                device = SignalSource(value["address"], value["device_type"])
            devs[key] = value
            devs[key]["device"] = device
            logging.info("Added {} to active devices dict".format(key)
                         .ljust(65, '.') + '[done]')
        else:
            devs[key]['channels'] = value['channels']
            logging.info("Updated {} in active devices dict".format(key)
                         .ljust(65, '.') + '[done]')
    return devs


def set_all_static_params(devs: Dict[str, Any]) -> None:
    """Set all values requested for static devices"""
    for value in devs.values():
        for channel, channel_values in value["channels"].items():
            value["device"].set_frequency(
                float(channel_values["frequency"]), int(channel[-1])
            )
            value["device"].set_amplitude(
                float(channel_values["amplitude"]), int(channel[-1])
            )


def set_all_dynamic_params(dynamic_devices: Dict[str, Any],
                           index_value: Dict[str, Any]) -> None:
    """Set all values requested for dynamic devices.
    This is a function of the sweep value index."""
    for value in dynamic_devices.values():
        for channel, channel_values in value["channels"].items():
            try:
                value["device"].set_frequency(
                    float(
                        channel_values["frequency_sweep_values"][index_value]),
                    channel[-1],
                )
            except Exception as e:
                print(e)
                pass
            try:
                value["device"].set_amplitude(
                    float(
                        channel_values["amplitude_sweep_values"][index_value]),
                    channel[-1],
                )
            except:
                continue


def make_sweep_lists(dynamic_devices: Dict[str, Any],
                     steps: int) -> Dict[str, Any]:
    """Contruct array / listof values to be sweeped"""
    for device_values in dynamic_devices.values():
        for channel_values in device_values["channels"].values():
            try:
                if channel_values["min_amplitude"] is not None:
                    channel_values["amplitude_sweep_values"] = np.linspace(
                        float(channel_values["min_amplitude"]),
                        float(channel_values["max_amplitude"]),
                        steps,
                    )
                else:
                    x = np.linspace(0, 1, steps)
                    channel_values["amplitude_sweep_values"] = eval(
                        channel_values["functional_amplitude"]
                    )
            except:
                pass
            try:
                if channel_values["min_frequency"] is not None:
                    channel_values["frequency_sweep_values"] = np.linspace(
                        float(channel_values["min_frequency"]),
                        float(channel_values["max_frequency"]),
                        steps,
                    )
                else:
                    x = np.linspace(0, 1, steps)
                    channel_values["frequency_sweep_values"] = eval(
                        channel_values["functional_frequency"]
                    )
            except:
                pass
    return dynamic_devices


def get_device_dicts(content: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    static_devices_requested = content["static_devices"]
    dynamic_devices_requested = content["dynamic_devices"]
    if static_devices_requested is None:
        static_devices_requested = {}
    if dynamic_devices_requested is None:
        dynamic_devices_requested = {}
    return copy.deepcopy(static_devices_requested), copy.deepcopy(dynamic_devices_requested)


def get_iterator_size(dynamic_devices: Dict[str, Any]) -> int:
    if dynamic_devices:
        for devices in dynamic_devices.values():
            for channel in devices["channels"].values():
                try:
                    iterator_size = len(channel["frequency_sweep_values"])
                except:
                    iterator_size = len(channel["amplitude_sweep_values"])
                break
            break
    if not dynamic_devices:
        iterator_size = 1
    return iterator_size
