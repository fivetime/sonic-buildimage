#!/usr/bin/env python

########################################################################
# DellEMC Z9100
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Fan-Drawers' information available in the platform.
#
########################################################################

try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

Z9100_FANS_PER_FANTRAY = 2


class FanDrawer(FanDrawerBase):
    """DellEMC Platform-specific Fan Drawer class"""

    def __init__(self, fantray_index):

        FanDrawerBase.__init__(self)
        # FanTray is 1-based in DellEMC platforms
        self.fantrayindex = fantray_index + 1
        for i in range(Z9100_FANS_PER_FANTRAY):
            self._fan_list.append(Fan(fantray_index, i))

    def get_name(self):
        """
        Retrieves the fan drawer name
        Returns:
            string: The name of the device
        """
        return "FanTray{}".format(self.fantrayindex)

    def get_presence(self):
        """
        Retrieves the presence of the fan drawer.
        A fan tray is present when its first fan is detected.
        """
        return self.get_fan(0).get_presence()

    def get_model(self):
        """
        Retrieves the part number of the fan drawer.
        """
        return self.get_fan(0).get_model()

    def get_serial(self):
        """
        Retrieves the serial number of the fan drawer.
        """
        return self.get_fan(0).get_serial()

    def get_status(self):
        """
        Retrieves the operational status of the fan drawer.
        """
        return self.get_fan(0).get_status()

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent device.
        """
        return self.fantrayindex

    def is_replaceable(self):
        """
        Indicate whether this fan drawer is replaceable.
        """
        return True

    def set_status_led(self, color):
        """
        Set led to expected color.
        Fan LEDs are controlled by the Smart-Fusion FPGA; return True to
        avoid a spurious thermalctld alarm.
        """
        return True

    def get_status_led(self):
        """
        Gets the state of the fan drawer status LED.
        """
        if self.get_presence():
            if self.get_fan(0).get_status():
                return self.STATUS_LED_COLOR_GREEN
            else:
                return self.STATUS_LED_COLOR_AMBER
        else:
            return self.STATUS_LED_COLOR_OFF

    def get_maximum_consumed_power(self):
        """
        Retrieves the maximum power drawn by this fan drawer.
        """
        return 54.0
