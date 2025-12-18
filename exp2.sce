clear;

NameOfNetwork = 'Hybrid_Ring_Star_Mesh';
NumberOfNodes = 16;

X = [400 500 600 600 500 400, ...
     300 250 350, ...
     700 750 650, ...
     300 500 700 500];

Y = [500 600 500 400 300 400, ...
     600 650 650, ...
     600 650 650, ...
     200 150 200 250];

head = [1 2 3 4 5 6, ...
        2 2 2, ...
        5 5 5, ...
        13 13 14 15];

tail = [2 3 4 5 6 1, ...
        7 8 9, ...
        10 11 12, ...
        14 15 16 16];

G = NL_G_MakeGraph(NameOfNetwork, NumberOfNodes, head, tail, X, Y);

NL_G_ShowGraph(G,1);
xtitle("Hybrid Ring + Dual Star + Mesh","X","Y");

NL_G_ShowGraphNE(G,2);
xtitle("Node & Edge Indices","X","Y");

NL_G_HighlightNodes(G,1:6,30,8,20,3);

meshEdges = [];
meshEdges = [meshEdges NL_G_Nodes2Edge(G,13,14)];
meshEdges = [meshEdges NL_G_Nodes2Edge(G,13,15)];
meshEdges = [meshEdges NL_G_Nodes2Edge(G,14,16)];
meshEdges = [meshEdges NL_G_Nodes2Edge(G,15,16)];

NL_G_HighlightEdges(G, meshEdges, 5, 6, 4);

[nnodes, nedges] = NL_G_GraphSize(G);
disp("Number of nodes: "+string(nnodes));
disp("Number of edges: "+string(nedges));

len = NL_G_EdgesLength(G.node_x, G.node_y, G.head, G.tail);
disp(len);
