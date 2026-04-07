#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

using namespace ns3;

// Server receive logic
void ReceivePacket (Ptr<Socket> socket)
{
    Ptr<Packet> packet;
    while ((packet = socket->Recv ()))
    {
        std::cout << "TCP Server received " << packet->GetSize ()
                  << " bytes at " << Simulator::Now ().GetSeconds () << " s\n";
    }
}

// Connection acceptance logic
void HandleAccept (Ptr<Socket> socket, const Address& from)
{
    socket->SetRecvCallback (MakeCallback (&ReceivePacket));
}

// Sending logic
void SendPacket (Ptr<Socket> socket, uint32_t pktSize, uint32_t pktCount, Time pktInterval)
{
    if (pktCount > 0)
    {
        socket->Send (Create<Packet> (pktSize));
        Simulator::Schedule (pktInterval, &SendPacket, socket, pktSize, pktCount - 1, pktInterval);
    }
    else
    {
        socket->Close ();
    }
}

int main (int argc, char *argv[])
{
    CommandLine cmd;
    cmd.Parse (argc, argv);

    NodeContainer nodes;
    nodes.Create (2);

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute ("DataRate", StringValue ("5Mbps"));
    p2p.SetChannelAttribute ("Delay", StringValue ("2ms"));

    NetDeviceContainer devices = p2p.Install (nodes);

    InternetStackHelper internet;
    internet.Install (nodes);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase ("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces = ipv4.Assign (devices);

    uint16_t port = 8080;

    // --- TCP SERVER SETUP ---
    Ptr<Socket> welcomeSocket = Socket::CreateSocket (nodes.Get (1), TcpSocketFactory::GetTypeId ());
    welcomeSocket->Bind (InetSocketAddress (Ipv4Address::GetAny (), port));
    welcomeSocket->Listen ();
    welcomeSocket->SetAcceptCallback (MakeNullCallback<bool, Ptr<Socket>, const Address&> (),
                                      MakeCallback (&HandleAccept));

    // --- TCP CLIENT SETUP ---
    Ptr<Socket> clientSocket = Socket::CreateSocket (nodes.Get (0), TcpSocketFactory::GetTypeId ());
    
    // Connect to Node 1's IP
    Simulator::Schedule (Seconds (1.0), &Socket::Connect, clientSocket, 
                         InetSocketAddress (interfaces.GetAddress (1), port));

    // Send data starting at 2s
    Simulator::Schedule (Seconds (2.0), &SendPacket, clientSocket, 1024, 10, Seconds (1.0));

    Simulator::Stop (Seconds (15.0));
    Simulator::Run ();
    Simulator::Destroy ();

    return 0;
}

