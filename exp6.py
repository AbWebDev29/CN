from scapy.all import rdpcap, IP, raw

def manual_checksum(ip_header_bytes):
    # If the header is 20 bytes, we have ten 16-bit words
    words = []
    for i in range(0, len(ip_header_bytes), 2):
        # Combine two 8-bit bytes into one 16-bit word
        word = (ip_header_bytes[i] << 8) + ip_header_bytes[i+1]
        words.append(word)
    
    # Sum all 16-bit words
    total_sum = sum(words)
    
    # Handle the carry (Keep only 16 bits and add the overflow back)
    while (total_sum >> 16):
        total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)
    
    # One's complement (flip the bits)
    final_checksum = (~total_sum) & 0xFFFF
    return final_checksum

def run_experiment(pcap_file):
    packets = rdpcap(pcap_file)
    print(f"{'ID':<4} | {'Field: Source':<15} | {'Field: Dest':<15} | {'Calc Chksum'}")
    print("-" * 60)

    for i, pkt in enumerate(packets[:20]): # Showing first 20 for brevity
        if IP in pkt:
            ip = pkt[IP]
            
            # Step 1: Create a copy and zero out the checksum field
            temp_pkt = ip.copy()
            temp_pkt.chksum = 0
            
            # Step 2: Get the raw bytes of the header (usually first 20 bytes)
            # We use 'raw(temp_pkt)[:20]' to isolate the header fields
            header_bytes = raw(temp_pkt)[:20]
            
            # Step 3: Calculate using the algorithm
            calculated = manual_checksum(header_bytes)
            
            print(f"{i:<4} | {ip.src:<15} | {ip.dst:<15} | {hex(calculated)}")

run_experiment('exp6.pcap')
