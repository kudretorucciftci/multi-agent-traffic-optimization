import os
import random
import sumolib

def generate_route_file(net_file, output_file, total_vehicles=500, initial_burst=150):
    print(f"Loading network: {net_file}...")
    net = sumolib.net.readNet(net_file)
    
    # Tüm binek araç geçebilen yollar
    all_edges = [e.getID() for e in net.getEdges() if e.allows("passenger")]
    
    # Merkezi/Işıklı Yollar: Trafik ışığına çıkan veya çok şeritli yollar
    central_edges = []
    for edge in net.getEdges():
        if edge.allows("passenger"):
            to_node = edge.getToNode()
            if to_node.getType() == "traffic_light" or edge.getLaneNumber() >= 2:
                central_edges.append(edge.getID())
    
    if not central_edges:
        central_edges = all_edges

    print(f"Generating scenario: Total={total_vehicles}, MASSIVE Start={initial_burst}")
    with open(output_file, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        
        # Tipler
        f.write('    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="50" guiShape="passenger" color="1,1,0"/>\n')
        
        # 1. BAŞLANGIÇ (Saniye 0): 150 Araç (Tüm ışıklı kavşaklarda yoğun birikme)
        for i in range(initial_burst):
            v_id = f"veh_start_{i}"
            depart = 0.00
            from_edge = random.choice(central_edges)
            to_edge = random.choice(all_edges)
            while to_edge == from_edge:
                to_edge = random.choice(all_edges)
            f.write(f'    <trip id="{v_id}" type="car" depart="{depart:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
        
        # 2. HIZLI AKIŞ: Geriye kalan 350 araç (Hemen ilk 60 saniyede yola çıksın)
        for i in range(total_vehicles - initial_burst):
            v_id = f"veh_flow_{i}"
            depart = random.uniform(0.1, 60.0)
            from_edge = random.choice(all_edges)
            to_edge = random.choice(all_edges)
            while to_edge == from_edge:
                to_edge = random.choice(all_edges)
            f.write(f'    <trip id="{v_id}" type="car" depart="{depart:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
        
        f.write('</routes>\n')
    print(f"Successfully created {output_file} with {total_vehicles} vehicles.")

if __name__ == "__main__":
    net_path = "maltepe.net.xml"
    route_path = "maltepe.rou.xml"
    generate_route_file(net_path, route_path, 500, 150)
