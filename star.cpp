#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/netanim-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("StarTopology");

int main(int argc, char *argv[]) {
    NodeContainer center;
    center.Create(1);
    NodeContainer leaves;
    leaves.Create(19);
    NodeContainer allNodes = NodeContainer(center.Get(0), leaves);

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("5Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("2ms"));

    NetDeviceContainer devices;
    for (uint32_t i = 0; i < 19; ++i) {
        devices.Add(p2p.Install(center.Get(0), leaves.Get(i)));
    }

    InternetStackHelper stack;
    stack.Install(allNodes);

    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces;
    for (uint32_t i = 0; i < 19; ++i) {
        interfaces.Add(address.Assign(devices.Get(2 * i), devices.Get(2 * i + 1)));
        address.NewNetwork();
    }

    UdpEchoServerHelper echoServer(9);
    ApplicationContainer serverApps = echoServer.Install(center.Get(0));
    serverApps.Start(Seconds(1.0));
    serverApps.Stop(Seconds(10.0));

    UdpEchoClientHelper echoClient(interfaces.GetAddress(0), 9);
    echoClient.SetAttribute("MaxPackets", UintegerValue(1));
    echoClient.SetAttribute("Interval", TimeValue(Seconds(1.0)));
    ApplicationContainer clientApps = echoClient.Install(leaves.Get(0));
    clientApps.Start(Seconds(2.0));
    clientApps.Stop(Seconds(10.0));

    AnimationInterface anim("star-topology.xml");
    anim.SetMaxPktsPerTraceFile(1000000);
    anim.SetConstantPosition(center.Get(0), 50.0, 50.0);
    for (uint32_t i = 0; i < 19; ++i) {
        double angle = i * 2 * 3.14159 / 19;
        anim.SetConstantPosition(leaves.Get(i), 50 + 40 * cos(angle), 50 + 40 * sin(angle));
    }

    Simulator::Stop(Seconds(10.0));
    Simulator::Run();
    Simulator::Destroy();
    return 0;
}
