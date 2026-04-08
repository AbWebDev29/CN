
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("MultiClientUDP");

// --- UDP SERVER ---
class UdpEchoServerApp : public Application {
public:
    UdpEchoServerApp() : m_socket(0) {}
    void Setup(uint16_t port) { m_port = port; }

private:
    virtual void StartApplication() {
        m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
        m_socket->Bind(InetSocketAddress(Ipv4Address::GetAny(), m_port));
        m_socket->SetRecvCallback(MakeCallback(&UdpEchoServerApp::HandleRead, this));
    }

    void HandleRead(Ptr<Socket> socket) {
        Ptr<Packet> packet;
        Address from;
        while ((packet = socket->RecvFrom(from))) {
            double now = Simulator::Now().GetSeconds();
            // Server Calculation: Logic for the lab
            double result = packet->GetSize() * 8.0; 
            
            std::stringstream msg;
            msg << "UDP_ACK | Time: " << now << "s | Bits: " << result;
            std::string response = msg.str();
            
            Ptr<Packet> responsePkt = Create<Packet>((uint8_t*)response.c_str(), response.length());
            socket->SendTo(responsePkt, 0, from);
        }
    }
    Ptr<Socket> m_socket;
    uint16_t m_port;
};

// --- UDP CLIENT ---
class UdpEchoClientApp : public Application {
public:
    UdpEchoClientApp() : m_socket(0) {}
    void Setup(Address peer, Time interval, std::string name) {
        m_peer = peer; m_interval = interval; m_name = name;
    }

private:
    virtual void StartApplication() {
        m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
        m_socket->Connect(m_peer);
        m_socket->SetRecvCallback(MakeCallback(&UdpEchoClientApp::HandleResponse, this));
        SendData();
    }

    void SendData() {
        std::string msg = "UDP Data from " + m_name;
        m_socket->Send(Create<Packet>((uint8_t*)msg.c_str(), msg.length()));
        Simulator::Schedule(m_interval, &UdpEchoClientApp::SendData, this);
    }

    void HandleResponse(Ptr<Socket> socket) {
        Ptr<Packet> packet = socket->Recv();
        NS_LOG_UNCOND("[" << m_name << "] UDP Response Received.");
    }
    Ptr<Socket> m_socket;
    Address m_peer;
    Time m_interval;
    std::string m_name;
};

int main(int argc, char *argv[]) {
    NodeContainer nodes;
    nodes.Create(3); 

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("10Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("5ms"));

    NetDeviceContainer d10 = p2p.Install(nodes.Get(1), nodes.Get(0));
    NetDeviceContainer d20 = p2p.Install(nodes.Get(2), nodes.Get(0));

    InternetStackHelper stack;
    stack.Install(nodes);

    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i10 = address.Assign(d10);
    address.SetBase("10.2.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i20 = address.Assign(d20);

    Ptr<UdpEchoServerApp> server = CreateObject<UdpEchoServerApp>();
    server->Setup(4000);
    nodes.Get(0)->AddApplication(server);

    Ptr<UdpEchoClientApp> clientA = CreateObject<UdpEchoClientApp>();
    clientA->Setup(InetSocketAddress(i10.GetAddress(1), 4000), Seconds(1.0), "CLIENT_A");
    nodes.Get(1)->AddApplication(clientA);

    Ptr<UdpEchoClientApp> clientB = CreateObject<UdpEchoClientApp>();
    clientB->Setup(InetSocketAddress(i20.GetAddress(1), 4000), Seconds(2.0), "CLIENT_B");
    nodes.Get(2)->AddApplication(clientB);

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    NS_LOG_UNCOND("--- Running UDP Simulation ---");
    Simulator::Stop(Seconds(10.0));
    Simulator::Run();

    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

    for (auto const& [id, stat] : stats) {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(id); // Fixed for 3.47
        std::cout << "Flow " << id << " (" << t.sourceAddress << " -> " << t.destinationAddress << ")\n";
        
        double duration = stat.timeLastRxPacket.GetSeconds() - stat.timeFirstTxPacket.GetSeconds(); // Fixed for 3.47
        if (duration > 0) {
            std::cout << "  Throughput: " << (stat.rxBytes * 8.0 / duration / 1024) << " Kbps\n";
        }
        std::cout << "  Packets Lost: " << stat.lostPackets << "\n";
    }

    Simulator::Destroy();
    return 0;
}
