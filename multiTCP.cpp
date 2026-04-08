
 #include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include <vector>
#include <string>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("MultiClientTCP");

// SERVER APPLICATION
class TcpChatServer : public Application {
public:
    TcpChatServer() : m_socket(0), m_port(9000) {}
    void Setup(uint16_t port) { m_port = port; }
private:
    virtual void StartApplication() {
        m_socket = Socket::CreateSocket(GetNode(), TcpSocketFactory::GetTypeId());
        m_socket->Bind(InetSocketAddress(Ipv4Address::GetAny(), m_port));
        m_socket->Listen();
        m_socket->SetAcceptCallback(MakeNullCallback<bool, Ptr<Socket>, const Address&>(),
                                    MakeCallback(&TcpChatServer::HandleAccept, this));
    }
    void HandleAccept(Ptr<Socket> s, const Address& from) {
        s->SetRecvCallback(MakeCallback(&TcpChatServer::HandleRead, this));
    }
    void HandleRead(Ptr<Socket> socket) {
        Ptr<Packet> packet;
        while ((packet = socket->Recv())) {
            double now = Simulator::Now().GetSeconds();
            std::stringstream msg;
            msg << "TCP_ACK | ServerTime: " << now << "s | PktSize: " << packet->GetSize();
            std::string response = msg.str();
            Ptr<Packet> responsePkt = Create<Packet>((uint8_t*)response.c_str(), response.length());
            socket->Send(responsePkt);
        }
    }
    Ptr<Socket> m_socket; uint16_t m_port;
};

// CLIENT APPLICATION
class TcpChatClient : public Application {
public:
    TcpChatClient() : m_socket(0) {}
    void Setup(Address peer, Time interval, std::string name) {
        m_peer = peer; m_interval = interval; m_name = name;
    }
private:
    virtual void StartApplication() {
        m_socket = Socket::CreateSocket(GetNode(), TcpSocketFactory::GetTypeId());
        m_socket->Connect(m_peer);
        m_socket->SetRecvCallback(MakeCallback(&TcpChatClient::HandleResponse, this));
        SendChat();
    }
    void SendChat() {
        if (m_socket) {
            std::string msg = "Hello from " + m_name;
            m_socket->Send(Create<Packet>((uint8_t*)msg.c_str(), msg.length()));
            Simulator::Schedule(m_interval, &TcpChatClient::SendChat, this);
        }
    }
    void HandleResponse(Ptr<Socket> socket) {
        Ptr<Packet> packet = socket->Recv();
        NS_LOG_UNCOND("[" << m_name << "] Received response from Server.");
    }
    Ptr<Socket> m_socket; Address m_peer; Time m_interval; std::string m_name;
};

int main(int argc, char *argv[]) {
    NodeContainer nodes;
    nodes.Create(3); // 0=Server, 1=ClientA, 2=ClientB

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("5Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("2ms"));

    NetDeviceContainer d10 = p2p.Install(nodes.Get(1), nodes.Get(0));
    NetDeviceContainer d20 = p2p.Install(nodes.Get(2), nodes.Get(0));

    InternetStackHelper stack;
    stack.Install(nodes);

    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i10 = address.Assign(d10);
    address.SetBase("10.2.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i20 = address.Assign(d20);

    Ptr<TcpChatServer> server = CreateObject<TcpChatServer>();
    server->Setup(9000);
    nodes.Get(0)->AddApplication(server);

    Ptr<TcpChatClient> clientA = CreateObject<TcpChatClient>();
    clientA->Setup(InetSocketAddress(i10.GetAddress(1), 9000), Seconds(2.0), "CLIENT_A");
    nodes.Get(1)->AddApplication(clientA);

    Ptr<TcpChatClient> clientB = CreateObject<TcpChatClient>();
    clientB->Setup(InetSocketAddress(i20.GetAddress(1), 9000), Seconds(4.0), "CLIENT_B");
    nodes.Get(2)->AddApplication(clientB);

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    NS_LOG_UNCOND("--- Running TCP Simulation ---");
    Simulator::Stop(Seconds(10.0));
    Simulator::Run();

    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

    for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin(); i != stats.end(); ++i) {
        // FIXED FOR 3.47: FindFlow
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(i->first); 
        std::cout << "Flow " << i->first << " (" << t.sourceAddress << " -> " << t.destinationAddress << ")\n";
        
        // FIXED FOR 3.47: timeLastRxPacket and timeFirstTxPacket
        double duration = i->second.timeLastRxPacket.GetSeconds() - i->second.timeFirstTxPacket.GetSeconds();
        if (duration > 0) {
            std::cout << "  Throughput: " << (i->second.rxBytes * 8.0) / duration / 1024  << " Kbps\n";
        }
        std::cout << "  Packets Lost: " << i->second.lostPackets << "\n";
    }

    Simulator::Destroy();
    return 0;
}
