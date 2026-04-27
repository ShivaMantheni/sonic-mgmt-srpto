from scapy.all import *
import time

# Configuration - DENIED SOURCE MAC
SRC_MAC = "00:AA:AA:AA:AA:01"  # This will be DENIED by rule 10
DST_MAC = "00:BB:BB:BB:BB:02"
VLAN_ID = 10
TX_IFACE = "eno1"  # Your TX interface
TX_COUNT = 10
INTERVAL = 0.05

# Build packet with VLAN tag
packet = Ether(src=SRC_MAC, dst=DST_MAC) / Dot1Q(vlan=VLAN_ID) / IP(src="10.0.0.1", dst="20.0.0.2") / ICMP()

# Transmit
print(f"Test 1: Sending {TX_COUNT} packets with DENIED source MAC {SRC_MAC}...")
for i in range(TX_COUNT):
    sendp(packet, iface=TX_IFACE, verbose=False)
    time.sleep(INTERVAL)
    print(f"  Sent packet {i+1}/{TX_COUNT}")

print("✓ Transmission complete!")
print(f"Expected RX: 0 packets (all dropped by rule 10)")
print(f"Test Result: PASS ✓ (if RX = 0)")


