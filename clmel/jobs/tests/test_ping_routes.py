from pyats import aetest
from genie.testbed import load as load_testbed
import re

# ------------------ Common Setup ------------------
class CommonSetup(aetest.CommonSetup):

    @aetest.subsection
    def connect_to_all(self, testbed):
        # Load and connect to all devices
        tb = load_testbed(testbed) if isinstance(testbed, str) else testbed
        self.parent.parameters['tb'] = tb

        for name, dev in tb.devices.items():
            dev.connect(log_stdout=False)


# ------------------ Testcase 1: Ping specific IP ------------------
class PingGateway(aetest.Testcase):

    @aetest.test
    def ping_gateway(self):
        tb = self.parent.parameters['tb']
        target_ip = "192.168.1.1"   # 👈 Change here if you want another target

        errors = []
        for name, dev in tb.devices.items():
            out = dev.execute(f"ping {target_ip} repeat 5 timeout 2")
            match = re.search(r"Success +rate +is +(\d+) +percent", out, re.I)
            if not match or int(match.group(1)) < 100:
                errors.append(f"{name} failed to ping {target_ip}: {out.strip().splitlines()[-1]}")

        if errors:
            self.failed("Ping test failures:\n" + "\n".join(errors))


# ------------------ Testcase 2: Static routes equal ------------------
class StaticRoutesEqual(aetest.Testcase):

    def get_static_routes(self, dev):
        try:
            out = dev.execute("show ip route static")
        except Exception:
            out = dev.execute("show ip route")
        return {m.group(1) for m in re.finditer(r"S\s+(\d+\.\d+\.\d+\.\d+/\d+)", out)}

    @aetest.test
    def compare_routes(self):
        tb = self.parent.parameters['tb']
        devices = list(tb.devices.values())

        if len(devices) < 2:
            self.skipped("Need at least 2 devices to compare")

        baseline = self.get_static_routes(devices[0])
        diffs = []
        for dev in devices[1:]:
            routes = self.get_static_routes(dev)
            if routes != baseline:
                diffs.append(f"{dev.name} differs: {routes ^ baseline}")

        if diffs:
            self.failed("Route mismatches:\n" + "\n".join(diffs))


# ------------------ Common Cleanup ------------------
class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def disconnect_all(self):
        tb = self.parent.parameters['tb']
        for dev in tb.devices.values():
            try:
                dev.disconnect()
            except Exception:
                pass

