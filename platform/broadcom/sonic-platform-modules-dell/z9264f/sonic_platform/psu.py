#!/usr/bin/env python

########################################################################
# DellEMC Z9264
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs' information which are available in the platform
#
########################################################################


try:
    from sonic_platform_base.psu_base import PsuBase
    from sonic_platform.ipmihelper import IpmiSensor, IpmiFru
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Psu(PsuBase):
    """DellEMC Platform-specific PSU class"""

    # { PSU-ID: { Sensor-Name: Sensor-ID } }
    SENSOR_MAPPING = { 1: { "State": 0x31, "Current": 0x39,
                            "Power": 0x37, "Voltage": 0x38,
                            "Temperature": 0x40 },
                       2: { "State": 0x32, "Current": 0x3F,
                            "Power": 0x3D, "Voltage": 0x3E,
                            "Temperature": 0x41 } }
    # ( PSU-ID: FRU-ID }
    FRU_MAPPING = { 1: 6, 2: 7 }

    def __init__(self, psu_index):
        PsuBase.__init__(self)
        # PSU is 1-based in DellEMC platforms
        self.index = psu_index + 1
        self.state_sensor = IpmiSensor(self.SENSOR_MAPPING[self.index]["State"],
                                       is_discrete=True)
        self.voltage_sensor = IpmiSensor(self.SENSOR_MAPPING[self.index]["Voltage"])
        self.current_sensor = IpmiSensor(self.SENSOR_MAPPING[self.index]["Current"])
        self.power_sensor = IpmiSensor(self.SENSOR_MAPPING[self.index]["Power"])
        self.temp_sensor = IpmiSensor(self.SENSOR_MAPPING[self.index]["Temperature"])
        self.fru = IpmiFru(self.FRU_MAPPING[self.index])

        self._fan_list.append(Fan(fan_index=self.index, psu_fan=True,
            dependency=self))

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "PSU{}".format(self.index)

    def get_presence(self):
        """
        Retrieves the presence of the Power Supply Unit (PSU)

        Returns:
            bool: True if PSU is present, False if not
        """
        presence = False
        is_valid, state = self.state_sensor.get_reading()
        if is_valid:
           if (state & 0b1):
                presence = True

        return presence

    def get_model(self):
        """
        Retrieves the part number of the PSU

        Returns:
            string: Part number of PSU
        """
        return self.fru.get_board_part_number()

    def get_serial(self):
        """
        Retrieves the serial number of the PSU

        Returns:
            string: Serial number of PSU
        """
        return self.fru.get_board_serial()

    def get_mfr_id(self):
        """
        Retrieves the Manufacturer Id of PSU

        Returns:
            A string, the manufacturer id.
        """
        return self.fru.get_board_mfr_id()

    def get_type(self):
        """
        Retrieves the power type of PSU

        Returns:
            A string, PSU power type
        """
        info = self.fru.get_board_product().split(',')
        if 'AC' in info: return 'AC'
        if 'DC' in info: return 'DC'
        return 'Unknown'

    def get_status(self):
        """
        Retrieves the operational status of the PSU

        Returns:
            bool: True if PSU is operating properly, False if not
        """
        status = False
        is_valid, state = self.state_sensor.get_reading()
        if is_valid:
           if (state == 0x01):
                status = True

        return status

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        is_valid, voltage = self.voltage_sensor.get_reading()
        if not is_valid:
            voltage = 0

        return float(voltage)

    def get_voltage_low_threshold(self):
        """
        Returns PSU low threshold in Volts
        """
        # The Z9264F BMC exposes bogus placeholder voltage thresholds
        # (LowerCritical=0, UpperCritical=240) for the PSU output rail, so
        # do not trust IPMI here; use the 12V-rail limits DellEMC platforms
        # fall back to (see s5232f/s5248f/... psu.py).
        return 11.6

    def get_voltage_high_threshold(self):
        """
        Returns PSU high threshold in Volts
        """
        # See get_voltage_low_threshold: IPMI thresholds are placeholders on
        # this platform; return the 12V-rail high limit used by sibling
        # DellEMC platforms.
        return 12.8

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, electric current in amperes,
            e.g. 15.4
        """
        is_valid, current = self.current_sensor.get_reading()
        if not is_valid:
            current = 0

        return float(current)

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts,
            e.g. 302.6
        """
        is_valid, power = self.power_sensor.get_reading()
        if not is_valid:
            power = 0

        return float(power)

    def get_temperature(self):
        """
        Retrieves current temperature reading from PSU

        Returns:
            A float number of current temperature in Celsius up to
            nearest thousandth of one degree Celsius, e.g. 30.125
        """
        is_valid, temperature = self.temp_sensor.get_reading()
        if not is_valid:
            temperature = 0

        return float(temperature)

    def get_temperature_high_threshold(self):
        """
        Returns the high temperature threshold for PSU in Celsius
        """
        is_valid, high_threshold = self.temp_sensor.get_threshold("UpperCritical")
        if not is_valid:
            high_threshold = 105
        high_threshold = "{:.2f}".format(high_threshold)

        return float(high_threshold)

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU

        Returns:
            A boolean, True if PSU has stablized its output voltages and
            passed all its internal self-tests, False if not.
        """
        status = False
        is_valid, state = self.state_sensor.get_reading()
        if is_valid:
           if (state == 0x01):
                status = True

        return status
