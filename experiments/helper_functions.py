import cirq
from qualtran import Register, Signature
import numpy as np
import networkx as nx
from networkx.drawing import nx_pydot
import sympy
# create the register dict from the signature
def create_register_dict_from_signature(signature):
    register_dict = {}
    reg_index = 0
    for i in range(len(signature)):
        register_dict[signature[i].name] = cirq.LineQubit.range(reg_index, reg_index + signature[i].dtype.num_qubits)
        reg_index += signature[i].dtype.num_qubits

    return register_dict

def create_matrix_for_rz_gate(phase = np.pi/2):
    # return the real_part and imaginary_part of the matrix seperately in a string
    # the matrix is:
    # [exp(-i*phase/2),0],
    #  [0, exp(i*phase/2)]]
    # return the real_part and imaginary_part of the matrix seperately in a string
    real_part = np.cos(phase/2)
    imaginary_part = np.sin(phase/2)
    matrix_str = str([[real_part-imaginary_part*1j, 0], [0, real_part+imaginary_part*1j]])
    return matrix_str

def create_matrix_for_hadamard():
    # return the real_part and imaginary_part of the matrix seperately in a string
    # the matrix is:
    # [1/sqrt(2), 1/sqrt(2)],
    # [1/sqrt(2), -1/sqrt(2)]]
    real_part = 1/np.sqrt(2)
    matrix_str = str([[real_part, real_part], [real_part, -real_part]])
    
    return matrix_str

def create_matrix_for_x():
    return str([[0, 1], [1, 0]])

def create_matrix_for_y():
    return str([[0, -1j], [1j, 0]])

def create_matrix_for_z():
    return str([[1, 0], [0, -1]])

def create_digraph_from_circuit(circuit: cirq.Circuit) -> nx.DiGraph:
    """Create a digraph from a cirq circuit."""
    # turn the circuit into a dag and store it into a .dot file
    digraph = nx.DiGraph()

    # count the current nodes in the digraph
    node_index = 0

    cur_nodes_positions = {}
    qubits_indices = {}
    # add the qqubits to the digraph
    for qubit in circuit.all_qubits():
        # is_ancillary = qubit.is_ancillary()
        # print(qubit , str(qubit).startswith('_'))
        digraph.add_node(node_index, label=str(qubit), qubits = str(node_index), matrix="None", ancilla=str(qubit).startswith('_'))
        cur_nodes_positions[str(qubit)] = node_index
        qubits_indices[str(qubit)] = node_index
        node_index += 1

    # add the operations to the digraph
    for op in circuit.all_operations():
        # print(op)
        # parse the qubits interact with the operation
        # turn this And(q(0), q(1), _c(0)) into a list ['q(0)', 'q(1)', '_c(0)']
        # qubits_str = str(op) # And(q(0), q(1), _c(0))
        # # remove the substring before the first '(' and after the last ')' and preseve all the characters in between    
        # qubits_str = qubits_str[qubits_str.find('(')+1:qubits_str.rfind(')')]
        # # remove the space in the qubits_str
        # qubits_str = qubits_str.replace(' ', '')
        # # split the qubits_str by ', '
        # qubits = qubits_str.split(',')
        # print(qubits)
        
        label = str(op)
        matrix = "None"
        print("op.gate: ", op.gate)
        if op.gate == cirq.CNOT or str(op.gate) == "And" or str(op.gate) == "And†" or op.gate == cirq.X:
            matrix = create_matrix_for_x()
        elif op.gate == cirq.Y:
            matrix = create_matrix_for_y()
        elif op.gate == cirq.Z:
            matrix = create_matrix_for_z()
        elif str(op.gate).startswith("Rz"):
            # get the rads from the op.gate
            rads_str = str(op.gate).split("(")[1].split('π')[0]

# 2. Convert the SymPy expression to a float
            rads = float(rads_str)*np.pi
            print("op.gate.rads: ", rads)   
            matrix = create_matrix_for_rz_gate(rads)
        elif op.gate == cirq.H or str(op.gate) == "CH":
            matrix = create_matrix_for_hadamard()
        elif op.gate == cirq.T:
            matrix = create_matrix_for_rz_gate(np.pi/4)
        qubits = []
        for qubit in op.qubits:
            qubits.append(str(qubit))
        num_qubits = len(qubits)
        num_clbits=0
        qubits_list = []
        # print the qubits_index
        for qubit in op.qubits:
            # print("op.qubits: ", qubit)
            qubits_list.append(qubits_indices[str(qubit)])

        # turn the qubits_list into a string
        qubits_list_str = ','.join(str(qubit) for qubit in qubits_list)

        # check if the control logic is 1 or 0
        control_0_logic = []
        if isinstance(op.gate, cirq.ControlledGate):
            for index, control_value in enumerate(op.gate.control_values):
                if control_value == 0:
                    control_0_logic.append(index)
        elif str(op.gate) == "And" or str(op.gate) == "And†":
            if op.gate.cv1 == 0:
                control_0_logic.append(qubits_list[0])
            if op.gate.cv2 == 0:
                control_0_logic.append(qubits_list[1])
        
        # apply x gate to the control-0 logic to make it control-1 logic
        for qubit in control_0_logic:
            qubit_name = digraph.nodes[qubit]['label']
            digraph.add_node(node_index, label="X", qubits = str(qubit), matrix=create_matrix_for_x())
            cur_operation_node = node_index
            node_index += 1
            digraph.add_edge(cur_nodes_positions[qubit_name], cur_operation_node, label=str(qubit))
            # print(f"add edge: {cur_nodes_positions[qubit_name]} -> {cur_operation_node}")
            # update the current node position for this qubit
            cur_nodes_positions[qubit_name] = cur_operation_node
        
        # add the operation as a node to the digraph
        digraph.add_node(node_index, label=label, qubits = qubits_list_str, matrix=matrix)
        # print(f"add node: label={label}, qubits={qubits_list_str}, matrix={matrix}")
        cur_operation_node = node_index
        node_index += 1

        # add the edges to this operation
        for qubit in qubits:
            digraph.add_edge(cur_nodes_positions[qubit], cur_operation_node, label=str(qubits_indices[str(qubit)]))
            # print(f"add edge: {cur_nodes_positions[qubit]} -> {cur_operation_node}")
            # update the current node position for this qubit
            cur_nodes_positions[qubit] = cur_operation_node

        # apply x gate to the control-0 logic to make it control-1 logic
        for qubit in control_0_logic:
            qubit_name = digraph.nodes[qubit]['label']
            digraph.add_node(node_index, label="X", qubits = str(qubit), matrix=create_matrix_for_x())
            cur_operation_node = node_index
            node_index += 1
            digraph.add_edge(cur_nodes_positions[qubit_name], cur_operation_node, label=str(qubit))
            # print(f"add edge: {cur_nodes_positions[qubit_name]} -> {cur_operation_node}")
            # update the current node position for this qubit
            cur_nodes_positions[qubit_name] = cur_operation_node

    # connect all the operation nodes to the output node
    for index, node in enumerate(qubits_indices):
        # print("output node: ", node, index)
        digraph.add_node(node_index, label=str(node), qubits = str(index), matrix="None", ancilla=str(node).startswith('_'))
        cur_output_node = node_index
        node_index += 1

        digraph.add_edge(cur_nodes_positions[node], cur_output_node, label=str(index))
        # print(f"add edge: {cur_nodes_positions[node]} -> {cur_output_node}")

    return digraph

def save_digraph_to_dot(digraph: nx.DiGraph, filename: str):
    """Save the digraph to a dot file."""
    nx_pydot.write_dot(digraph, filename)
    return

def save_digraph_to_png(digraph: nx.DiGraph, filename: str):
    """Save the digraph to a png file."""
    nx_pydot.write_png(digraph, filename)
    return  