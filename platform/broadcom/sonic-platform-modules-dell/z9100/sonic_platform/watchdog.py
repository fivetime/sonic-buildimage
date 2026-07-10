########################################################################
# DELLEMC Z9100
#
# Platform-specific Watchdog class for the Z9100 hardware watchdog.
#
# The Z9100-ON has no BMC; its watchdog is the ACPI WDAT device exposed by
# the kernel "wdat_wdt" driver as /dev/watchdog*. This class drives it over
# the standard Linux watchdog ioctl / sysfs interface (unlike the Dell BMC
# platforms which drive the watchdog over IPMI).
########################################################################

try:
    import array
    import fcntl
    import glob
    import os
    from sonic_platform_base.watchdog_base import WatchdogBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

# Linux watchdog ioctl constants
IOC_WRITE = 0x40000000
IOC_READ = 0x80000000
IOC_SIZE_INT = 0x00040000
WATCHDOG_IOCTL_BASE = ord('W')
WDIOC_SETOPTIONS = IOC_READ | IOC_SIZE_INT | (WATCHDOG_IOCTL_BASE << 8) | 4
WDIOC_KEEPALIVE = IOC_READ | IOC_SIZE_INT | (WATCHDOG_IOCTL_BASE << 8) | 5
WDIOC_SETTIMEOUT = IOC_READ | IOC_WRITE | IOC_SIZE_INT | (WATCHDOG_IOCTL_BASE << 8) | 6
WDIOS_DISABLECARD = 0x0001
WDIOS_ENABLECARD = 0x0002


class Watchdog(WatchdogBase):
    """Z9100 hardware watchdog (ACPI wdat_wdt) via /dev/watchdog."""

    IDENTITY = "wdat_wdt"

    def __init__(self):
        self.dev = None
        self.dev_name = None
        wd_sysfs_path = "/sys/class/watchdog"

        # Prefer the device whose identity matches the Z9100 WDAT watchdog,
        # else fall back to the first available /dev/watchdog* device.
        for dev_file in sorted(glob.glob("/dev/watchdog*")):
            dev = os.path.basename(dev_file)
            if self._read_file("{}/{}/identity".format(wd_sysfs_path, dev)) == self.IDENTITY:
                self.dev_name = dev
                break
        if self.dev_name is None:
            devs = sorted(glob.glob("/dev/watchdog*"))
            if devs:
                self.dev_name = os.path.basename(devs[0])
        if self.dev_name is None:
            raise RuntimeError("no hardware watchdog device found")

        self.state_file = "{}/{}/state".format(wd_sysfs_path, self.dev_name)
        self.timeout_file = "{}/{}/timeout".format(wd_sysfs_path, self.dev_name)
        self.timeleft_file = "{}/{}/timeleft".format(wd_sysfs_path, self.dev_name)

    def __del__(self):
        if self.dev is not None:
            os.close(self.dev)

    def _ioctl(self, request, arg=0, mutate_flag=True):
        self._open_wd_dev()
        fcntl.ioctl(self.dev, request, arg, mutate_flag)

    def _open_wd_dev(self):
        if self.dev is None:
            self.dev = os.open("/dev/{}".format(self.dev_name), os.O_RDWR)

    @staticmethod
    def _read_file(file_path):
        try:
            with open(file_path, "r") as fd:
                return fd.read().strip()
        except (OSError, IOError):
            return -1

    def arm(self, seconds):
        if seconds < 0 or seconds > 0x3ff:
            return -1
        if seconds < 4:
            seconds = 4
        try:
            timeout = int(self._read_file(self.timeout_file))
            if timeout != seconds:
                buf = array.array('I', [seconds])
                self._ioctl(WDIOC_SETTIMEOUT, buf)
                timeout = int(buf[0])
            if self.is_armed():
                self._ioctl(WDIOC_KEEPALIVE)
            else:
                buf = array.array('h', [WDIOS_ENABLECARD])
                self._ioctl(WDIOC_SETOPTIONS, buf, False)
        except (OSError, IOError):
            return -1
        return timeout

    def disarm(self):
        disarmed = True
        if self.is_armed():
            try:
                buf = array.array('h', [WDIOS_DISABLECARD])
                self._ioctl(WDIOC_SETOPTIONS, buf, False)
            except (OSError, IOError):
                disarmed = False
        return disarmed

    def is_armed(self):
        return self._read_file(self.state_file) == "active"

    def get_remaining_time(self):
        timeleft = -1
        if self.is_armed():
            try:
                timeleft = int(self._read_file(self.timeleft_file))
            except (ValueError, TypeError):
                timeleft = -1
        return timeleft
