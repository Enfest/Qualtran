import cirq
from qualtran import Register, Signature

# create the register dict from the signature
def create_register_dict_from_signature(signature):
    register_dict = {}
    reg_index = 0
    for i in range(len(signature)):
        register_dict[signature[i].name] = cirq.LineQubit.range(reg_index, reg_index + signature[i].dtype.num_qubits)
        reg_index += signature[i].dtype.num_qubits

    return register_dict