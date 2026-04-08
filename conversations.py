import csv
import collections
import statistics
from scapy.all import *

# ==========================================
# CONFIGURATION
# ==========================================
PCAP_FILE = 'exp8.pcap'
CSV_OUTPUT_FILE = 'conversations.csv'

# Protocol Number Mapping (Common protocols)
PROTO_MAP = {1: 'ICMP', 6: 'TCP', 17: 'UDP', 2: 'IGMP', 89: 'OSPF'}

def get_proto_name(proto_num):
    return PROTO_MAP.get(proto_num, str(proto_num))

def main():
    print(f"Loading {PCAP_FILE}... (This may take a moment)")
    try:
        packets = rdpcap(PCAP_FILE)
    except FileNotFoundError:
        print(f"Error: '{PCAP_FILE}' not found. Please ensure the file is in the directory.")
        return

    print(f"Successfully loaded {len(packets)} packets. Analyzing conversations...\n")

    # Data Structures
    # Key: (IP_A, IP_B) -> Value: { 'bytes': 0, 'packets': 0 }
    ip_pair_totals = collections.defaultdict(lambda: {'bytes': 0, 'packets': 0})

    # Key: (IP_A, IP_B, Protocol) -> Value: { 'bytes': 0, 'packets': 0, 'timestamps': [] }
    conversation_details = collections.defaultdict(lambda: {'bytes': 0, 'packets': 0, 'timestamps': []})

    for pkt in packets:
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst
            proto_num = pkt[IP].proto
            proto_name = get_proto_name(proto_num)
            
            # Sort IP pair to ensure A->B and B->A are treated as the same conversation
            ip_pair = tuple(sorted((src, dst)))
            
            # Update Total Stats for the unique address pair
            ip_pair_totals[ip_pair]['bytes'] += len(pkt)
            ip_pair_totals[ip_pair]['packets'] += 1

            # Update Detailed Stats for the specific Protocol within the pair
            # Key includes Protocol now
            conv_key = (ip_pair[0], ip_pair[1], proto_name)
            
            conversation_details[conv_key]['bytes'] += len(pkt)
            conversation_details[conv_key]['packets'] += 1
            conversation_details[conv_key]['timestamps'].append(float(pkt.time))

    # ==========================================
    # 1. FIND ADDRESS PAIR WITH MAXIMUM BYTES
    # ==========================================
    if ip_pair_totals:
        max_pair = max(ip_pair_totals.items(), key=lambda x: x[1]['bytes'])
        max_ip_a, max_ip_b = max_pair[0]
        max_bytes_val = max_pair[1]['bytes']
        
        print(f"1. Unique Address Pair with Max Bytes:")
        print(f"   {max_ip_a} <--> {max_ip_b}  ({max_bytes_val} bytes)\n")
    else:
        print("No IP packets found.\n")

    # ==========================================
    # 2. CALCULATE AVERAGE INTER-PACKET TIME
    # ==========================================
    print("2. Average Inter-Packet Time & Total Packets (Per Pair & Protocol):")
    print(f"{'Address A':<16} {'Address B':<16} {'Proto':<6} {'Pkts':<6} {'Avg Time (s)':<15}")
    print("-" * 65)

    csv_rows = []

    for key, data in conversation_details.items():
        ip_a, ip_b, proto = key
        count = data['packets']
        total_bytes = data['bytes']
        timestamps = data['timestamps']
        
        # Calculate Average Inter-Packet Time
        if len(timestamps) > 1:
            # Calculate differences between consecutive packets
            diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            avg_inter_packet_time = statistics.mean(diffs)
        else:
            avg_inter_packet_time = 0.0

        print(f"{ip_a:<16} {ip_b:<16} {proto:<6} {count:<6} {avg_inter_packet_time:.6f}")

        # Prepare row for CSV
        csv_rows.append([ip_a, ip_b, proto, count, total_bytes, f"{avg_inter_packet_time:.6f}"])

    print("-" * 65)

    # ==========================================
    # 3. SAVE TO CSV
    # ==========================================
    try:
        with open(CSV_OUTPUT_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Address A', 'Address B', 'Protocol', 'Total Packets', 'Total Bytes', 'Avg Inter-Packet Time (s)'])
            writer.writerows(csv_rows)
        print(f"\nSuccessfully saved conversation details to '{CSV_OUTPUT_FILE}'")
    except IOError as e:
        print(f"Error saving CSV: {e}")

if __name__ == "__main__":
    main()
