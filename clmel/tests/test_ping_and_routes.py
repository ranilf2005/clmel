from pyats import aetest
from genie.testbed import load as load_testbed
import re

class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect_to_all(self, testbed):
        self.parent.parameters['testbed'] = testbed
        testbed = load_testbed(testbed) if isinstance(testbed, str) else testbed
        self.parent.parameters['tb'] = testbed
        for name, dev in testbed.devices.items():
            dev.connect(log_stdout=False)

class PingAll(aetest.Testcase):
    @aetest.test
    def ping_each_other(self, section, parent):
        tb = parent.parameters['tb']
        # Build a map: device -> its mgmt IP (from testbed connections.cli.ip)
        mgmt = {}
        for name, dev in tb.devices.items():
            ip = dev.connections['cli'].ip
            mgmt[name] = ip

        errors = []
        for src_name, src in tb.devices.items():
            for dst_name, dst_ip in mgmt.items():
                if src_name == dst_name:
                    continue
                section.uid = f"ping_{src_name}_to_{dst_name}"
                out = src.execute(f"ping {dst_ip} repeat 5 timeout 2")
                # Expect "Success rate is 100 percent"
                if re.search(r"Success +rate +is +100 +percent", out, re.I) is None:
                    errors.append(f"{src_name} -> {dst_name} ({dst_ip}) failed: {out.strip().splitlines()[-1]}")

        aetest.assert_msg(len(errors) == 0, "Ping failures detected:\n" + "\n".join(errors) if errors else "")

class StaticRoutesEqual(aetest.Testcase):
    def _get_static_routes(self, dev):
        # Try "show ip route static" first
        try:
            out = dev.execute("show ip route static")
            lines = out.splitlines()
            s_lines = [l.strip() for l in lines if l.strip().startswith('S')]
        except Exception:
            # Fallback: parse full table
            out = dev.execute("show ip route")
            lines = out.splitlines()
            s_lines = [l.strip() for l in lines if l.strip().startswith('S')]

        # Extract destination prefix from lines like:
        # S    10.1.0.0/24 [1/0] via 192.168.1.1
        prefixes = set()
        for l in s_lines:
            m = re.search(r"S\s+(\d+\.\d+\.\d+\.\d+\/\d+)", l)
            if m:
                prefixes.add(m.group(1))
        return prefixes

    @aetest.test
    def compare(self, parent):
        tb = parent.parameters['tb']
        dev_items = list(tb.devices.items())
        if len(dev_items) < 2:
            aetest.skip("Need at least 2 devices to compare routes")

        baseline_name, baseline_dev = dev_items[0]
        baseline = self._get_static_routes(baseline_dev)

        diffs = []
        for name, dev in dev_items[1:]:
            routes = self._get_static_routes(dev)
            if routes != baseline:
                diffs.append(f"{name} != {baseline_name}: {routes ^ baseline}")

        aetest.assert_msg(len(diffs) == 0, "Static route sets differ:\n" + "\n".join(diffs) if diffs else "")

class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect_all(self, parent):
        tb = parent.parameters['tb']
        for _, dev in tb.devices.items():
            try:
                dev.disconnect()
            except Exception:
                pass

