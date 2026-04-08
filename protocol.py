import csv
import collections
from scapy.all import *

# ==========================================
# CONFIGURATION
# ==========================================
PCAP_FILE = 'exp8.pcap'
CSV_OUTPUT_FILE = 'protocol_hierarchy.csv'

def get_protocol_name(pkt):
    """Returns the highest layer protocol name found in the packet."""
    
    # 1. Check for TCP-based protocols using Ports
    if pkt.haslayer(TCP):
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
        
        if sport == 80 or dport == 80: return "HTTP"
        if sport == 443 or dport == 443: return "TLS/SSL"
        if sport == 53 or dport == 53: return "DNS (TCP)"
        if sport == 21 or dport == 21: return "FTP"
        if sport == 22 or dport == 22: return "SSH"
        return "TCP"

    # 2. Check for UDP-based protocols using Ports
    if pkt.haslayer(UDP):
        sport = pkt[UDP].sport
        dport = pkt[UDP].dport
        
        if sport == 53 or dport == 53: return "DNS"
        if sport == 67 or dport == 67: return "DHCP"
        if sport == 68 or dport == 68: return "DHCP"
        return "UDP"

    # 3. Check for Lower Layer Protocols
    if pkt.haslayer(ICMP): return "ICMP"
    if pkt.haslayer(ARP): return "ARP"
    if pkt.haslayer(IP): return "IP"
    if pkt.haslayer(IPv6): return "IPv6"
    
    return "Ethernet/Other"

def main():
    print(f"Loading {PCAP_FILE}...")
    try:
        packets = rdpcap(PCAP_FILE)
    except FileNotFoundError:
        print(f"Error: '{PCAP_FILE}' not found. Make sure the file is in this folder.")
        return
    except Exception as e:
        print(f"An error occurred reading the file: {e}")
        return

    # Statistics Containers
    total_packets = len(packets)
    total_len = 0
    total_header_len = 0
    total_payload_len = 0

    # Dictionary for Protocol Hierarchy: {Protocol: {'packets': 0, 'bytes': 0}}
    proto_stats = collections.defaultdict(lambda: {'packets': 0, 'bytes': 0})

    print(f"Processing {total_packets} packets...")

    for pkt in packets:
        pkt_len = len(pkt)
        total_len += pkt_len

        # Estimate Payload (Data) Size
        # If the packet has a 'Raw' layer (payload), count it as data.
        if pkt.haslayer(Raw):
            payload_size = len(pkt.getlayer(Raw))
        else:
            payload_size = 0
            
        # Everything else is considered "Header" overhead
        header_size = pkt_len - payload_size

        total_payload_len += payload_size
        total_header_len += header_size

        # Categorize by Protocol
        proto_name = get_protocol_name(pkt)
        proto_stats[proto_name]['packets'] += 1
        proto_stats[proto_name]['bytes'] += pkt_len

    # ==========================================
    # 1. PRINT SUMMARY TO CONSOLE
    # ==========================================
    print("\n" + "=" * 40)
    print("PROTOCOL HIERARCHY SUMMARY")
    print("=" * 40)
    print(f"Total number of packets : {total_packets}")
    print(f"Size of data (Payload)  : {total_payload_len} bytes")
    print(f"Size of headers         : {total_header_len} bytes")
    print(f"Total size (on wire)    : {total_len} bytes")
    print("-" * 40)
    
    # Print a quick preview of the top protocols
    print(f"{'Protocol':<15} | {'Count':<10} | {'Bytes':<10}")
    print("-" * 40)
    sorted_preview = sorted(proto_stats.items(), key=lambda x: x[1]['bytes'], reverse=True)
    for proto, data in sorted_preview:
        print(f"{proto:<15} | {data['packets']:<10} | {data['bytes']:<10}")
    print("-" * 40)

    # ==========================================
    # 2. SAVE TO CSV
    # ==========================================
    try:
        with open(CSV_OUTPUT_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Header Row
            writer.writerow(['Protocol', 'Packet Count', 'Total Bytes', 'Percentage of Bytes'])
            
            # Sort by packet count descending
            sorted_stats = sorted(proto_stats.items(), key=lambda x: x[1]['bytes'], reverse=True)
            
            for proto, data in sorted_stats:
                percent = (data['bytes'] / total_len) * 100 if total_len > 0 else 0.0
                writer.writerow([
                    proto, 
                    data['packets'], 
                    data['bytes'], 
                    f"{percent:.2f}%"
                ])
        
        print(f"\nSuccessfully saved detailed stats to '{CSV_OUTPUT_FILE}'")

    except IOError as e:
        print(f"Error saving CSV file: {e}")

if __name__ == "__main__":
    main()
