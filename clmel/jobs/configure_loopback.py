import sys
import yaml
import argparse
from genie.testbed import load as load_testbed

def has_ip(dev, iface, ip):
    out = dev.execute("show ip interface brief")
    # Lines often look like: Loopback300     2.2.2.2     YES ...
    return (iface in out) and (ip in out)

def save_config(dev):
    try:
        dev.execute("write memory")
    except Exception:
        try:
            dev.execute("copy running-config startup-config\n\n")
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testbed", required=True)
    parser.add_argument("--config", required=True)  # configs/loopbacks.yaml
    args = parser.parse_args()

    tb = load_testbed(args.testbed)
    with open(args.config) as f:
        payload = yaml.safe_load(f)

    overall_ok = True

    for dev_name, interfaces in payload.get("devices", {}).items():
        if dev_name not in tb.devices:
            print(f"[WARN] Skipping {dev_name}: not found in testbed")
            overall_ok = False
            continue

        dev = tb.devices[dev_name]
        print(f"\n=== Connecting to {dev_name} ===")
        dev.connect(log_stdout=False)

        for iface in interfaces:
            name = iface["name"]
            ip = iface["ip"]
            mask = iface["mask"]

            if has_ip(dev, name, ip):
                print(f"[OK] {dev_name}: {name} already has {ip} — skipping")
                continue

            cfg = [
                f"interface {name}",
                f" ip address {ip} {mask}",
                "exit"
            ]
            print(f"[CFG] {dev_name}: configuring {name} {ip} {mask}")
            dev.configure("\n".join(cfg))
            save_config(dev)

            # Verify
            if has_ip(dev, name, ip):
                print(f"[OK] {dev_name}: verified {name} has {ip}")
            else:
                print(f"[ERROR] {dev_name}: verification failed for {name} {ip}")
                overall_ok = False

        try:
            dev.disconnect()
        except Exception:
            pass

    if not overall_ok:
        print("\nOne or more devices failed verification. Exiting 1.")
        sys.exit(1)

if __name__ == "__main__":
    main()

