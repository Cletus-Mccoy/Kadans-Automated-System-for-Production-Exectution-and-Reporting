import time
import random
import yaml
import csv
from opcua import Server

# Read variables from CSV
CSV_FILE = 'postgres/tagList_export.csv'
with open(CSV_FILE, newline='') as f:
    reader = csv.DictReader(f)
    variables = [row for row in reader]

# Setup OPC UA server
server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4840")

uri = "http://examples.org"
idx = server.register_namespace(uri)
print(f"Namespace URI: {uri}, index: {idx}")

objects = server.get_objects_node()
machine = objects.add_object(idx, "Machine")

# Add variables from CSV, set initial value based on type
node_vars = {}
for var in variables:
    name = var['Name']
    typ = var['Type'].upper()
    if typ == 'REAL':
        initial = 0.0
    elif typ == 'INT' or typ == 'DINT':
        initial = 0
    elif typ == 'BOOL':
        initial = False
    else:
        initial = ""
    node_vars[name] = machine.add_variable(idx, name, initial)

# Write NodeIds to file
nodeids = {name: node.nodeid.to_string() for name, node in node_vars.items()}
with open("/app/nodeids.yaml", "w") as f:
    yaml.dump(nodeids, f)

print("Created nodes:")
for name, node in node_vars.items():
    print(f"  {name} NodeId: {node.nodeid}")
    node.set_writable()

server.start()
print("Mock OPC UA server started at opc.tcp://127.0.0.1:4840")

try:
    while True:
        # Generate random values for each variable
        for var in variables:
            name = var['Name']
            typ = var['Type'].upper()
            if typ == 'REAL':
                value = random.uniform(15.0, 25.0)
            elif typ == 'INT' or typ == 'DINT':
                value = random.randint(0, 10)
            elif typ == 'BOOL':
                value = random.choice([True, False])
            else:
                # For attributive/text variables, randomize some values
                if name.lower() == 'color':
                    value = random.choice(["red", "green", "blue"])
                elif name.lower() == 'defecttype':
                    value = random.choice(["scratch", "dent", "none"])
                elif name.lower() == 'supplier':
                    value = random.choice(["TestSupplier", "SupplierA", "SupplierB"])
                elif name.lower() == 'batchid':
                    value = f"BATCH{random.randint(100,999)}"
                else:
                    value = ""
            node_vars[name].set_value(value)
        print("Set " + ", ".join(f"{k}={node_vars[k].get_value()}" for k in node_vars))
        time.sleep(2)
except KeyboardInterrupt:
    print("Shutting down mock OPC UA server...")
finally:
    server.stop()
