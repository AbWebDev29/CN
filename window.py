import matplotlib.pyplot as plt
import collections
from scapy.all import *

# ==========================================
# CONFIGURATION
# ==========================================
PCAP_FILE = 'exp8.pcap'

# TARGET IPs (For graphs 2, 3, 4, 5)
TARGET_IP_1 = "142.251.222.206"
TARGET_IP_2 = "192.168.137.139"

def is_target_packet(pkt):
    """Checks if packet belongs to the specific TCP stream"""
    if IP in pkt:
        src = pkt[IP].src
        dst = pkt[IP].dst
        return (src == TARGET_IP_1 and dst == TARGET_IP_2) or \
               (src == TARGET_IP_2 and dst == TARGET_IP_1)
    return False

def main():
    print(f"Loading {PCAP_FILE}...")
    try:
        all_packets = rdpcap(PCAP_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find '{PCAP_FILE}'.")
        return

    if not all_packets:
        print("Error: Capture file is empty.")
        return

    start_time = all_packets[0].time
    print(f"Total Packets: {len(all_packets)}")

    # ========================================================
    # GRAPH 1: IO STATISTICS (The 5-Line Graph you liked)
    # ========================================================
    print("Generating Graph 1: IO Statistics (5 Lines)...")
    
    graph_data = {
        'All': collections.defaultdict(int),
        'TCP': collections.defaultdict(int),
        'UDP': collections.defaultdict(int),
        'HTTP': collections.defaultdict(int),
        'ARP': collections.defaultdict(int)
    }

    for pkt in all_packets:
        time_bin = int(pkt.time - start_time)
        graph_data['All'][time_bin] += 1
        
        if pkt.haslayer(TCP):
            graph_data['TCP'][time_bin] += 1
            # Check common web ports (80=HTTP, 443=HTTPS)
            if pkt[TCP].dport in [80, 443] or pkt[TCP].sport in [80, 443]:
                graph_data['HTTP'][time_bin] += 1
        
        if pkt.haslayer(UDP):
            graph_data['UDP'][time_bin] += 1
            
        if pkt.haslayer(ARP):
            graph_data['ARP'][time_bin] += 1

    # Plot IO Graph
    max_time = max(graph_data['All'].keys()) if graph_data['All'] else 0
    x_axis = list(range(max_time + 1))
    
    plt.figure(figsize=(12, 6))
    plt.plot(x_axis, [graph_data['All'].get(t,0) for t in x_axis], label='All Traffic', color='black')
    plt.plot(x_axis, [graph_data['TCP'].get(t,0) for t in x_axis], label='TCP', color='red')
    plt.plot(x_axis, [graph_data['UDP'].get(t,0) for t in x_axis], label='UDP', color='blue')
    plt.plot(x_axis, [graph_data['HTTP'].get(t,0) for t in x_axis], label='HTTP/TLS', color='green')
    plt.plot(x_axis, [graph_data['ARP'].get(t,0) for t in x_axis], label='ARP', color='orange')
    
    plt.title('Graph 1: Network IO Statistics')
    plt.xlabel('Time (s)')
    plt.ylabel('Packets / sec')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('graph_1_io.png')
    print(" -> Saved 'graph_1_io.png'")

    # ========================================================
    # PREPARE FOR SPECIFIC GRAPHS (Filter for Target IPs)
    # ========================================================
    target_packets = [p for p in all_packets if is_target_packet(p) and TCP in p]

    if not target_packets:
        print("No packets found for the target IP connection. Skipping Graphs 2-5.")
        return

    print(f"\nProcessing {len(target_packets)} packets for TCP Analysis (Graphs 2-5)...")
    
    # Reset lists for specific graphs
    stevens_x, stevens_y = [], []
    win_x, win_y = [], []
    rtt_x, rtt_y = [], []
    throughput_buckets = collections.defaultdict(int)
    
    # Helpers
    isn = target_packets[0][TCP].seq # Initial Sequence Number
    unacked = {} # For RTT

    for pkt in target_packets:
        rel_time = float(pkt.time - start_time)
        tcp = pkt[TCP]

        # Graph 2: Stevens (Sequence Numbers)
        # Only plot traffic from Server -> Client (or Source -> Dest) to see the sequence rise
        if pkt[IP].src == TARGET_IP_1:
            stevens_x.append(rel_time)
            stevens_y.append(tcp.seq - isn)

        # Graph 3: Window Scaling
        win_x.append(rel_time)
        win_y.append(tcp.window * 128) # Scaling Factor 128

        # Graph 4: Throughput
        throughput_buckets[int(rel_time)] += (len(pkt) * 8)

        # Graph 5: RTT
        if len(tcp.payload) > 0:
            expected_ack = tcp.seq + len(tcp.payload)
            unacked[expected_ack] = rel_time
        
        if tcp.flags.A and tcp.ack in unacked:
            time_sent = unacked.pop(tcp.ack)
            rtt = rel_time - time_sent
            rtt_x.append(rel_time)
            rtt_y.append(rtt)

    # ================= PLOTTING GRAPHS 2-5 =================

    # Graph 2: Stevens
    plt.figure(figsize=(10, 5))
    plt.plot(stevens_x, stevens_y, 'ko', markersize=2)
    plt.title('Graph 2: Time / Sequence (Stevens)')
    plt.xlabel('Time (s)')
    plt.ylabel('Sequence Number')
    plt.grid(True, alpha=0.3)
    plt.savefig('graph_2_stevens.png')
    print(" -> Saved 'graph_2_stevens.png'")

    # Graph 3: Window Scaling
    plt.figure(figsize=(10, 5))
    plt.plot(win_x, win_y, color='green', drawstyle='steps-post')
    plt.title('Graph 3: Window Scaling')
    plt.xlabel('Time (s)')
    plt.ylabel('Window Size (Bytes)')
    plt.grid(True, alpha=0.3)
    plt.savefig('graph_3_window.png')
    print(" -> Saved 'graph_3_window.png'")

    # Graph 4: Throughput
    tp_times = sorted(throughput_buckets.keys())
    tp_vals = [throughput_buckets[t] for t in tp_times]
    plt.figure(figsize=(10, 5))
    plt.plot(tp_times, tp_vals, color='black', drawstyle='steps-mid')
    plt.fill_between(tp_times, tp_vals, step='mid', color='grey', alpha=0.3)
    plt.title('Graph 4: Throughput')
    plt.xlabel('Time (s)')
    plt.ylabel('Bits / Sec')
    plt.grid(True, alpha=0.3)
    plt.savefig('graph_4_throughput.png')
    print(" -> Saved 'graph_4_throughput.png'")

    # Graph 5: RTT
    plt.figure(figsize=(10, 5))
    if rtt_x:
        plt.plot(rtt_x, rtt_y, 'o', color='steelblue', markersize=3)
        plt.title('Graph 5: Round Trip Time (RTT)')
        plt.xlabel('Time (s)')
        plt.ylabel('RTT (s)')
        plt.grid(True, alpha=0.3)
        plt.savefig('graph_5_rtt.png')
        print(" -> Saved 'graph_5_rtt.png'")
    else:
        print(" -> Skipped RTT (No valid request/response pairs found)")

    print("\nDone! 5 graphs generated.")

if __name__ == "__main__":
    main()
