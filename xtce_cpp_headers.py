from __future__ import annotations
import enum

import yamcs.pymdb as Y

class SystemCppRepresentation:
    def __init__(self):
        self.filename = ""
        self.includes = ""
        self.system_globals = ""
        self.system_globals_list = []
        self.structs_definitions = ""

    def dumps(self):
        include_guard_header_name = self.filename.upper().replace(".", "_") + "_"
        include_guard = f"#ifndef {include_guard_header_name}\n#define {include_guard_header_name}\n\n"
        include_guard_end = f"#endif // {include_guard_header_name}\n"
        return "".join([include_guard, self.includes, self.system_globals, self.structs_definitions, include_guard_end])

def convert_fixed_value_entry_to_cpp_struct(
        entry : Y.FixedValueEntry,
        system_name : str,
        system_cpp_representation : SystemCppRepresentation
    ) -> None:
    """
    Convert a parameter entry to C++ headers and structs.

    Parameters
    ----------
    entry : Y.FixedValueEntry
        The XTCE fixed value entry to convert
    system_name : str
        The name of the system to which the entry belongs.
        Used to determine if the entry entry belongs to this current system. (TODO)
    system_cpp_representation : SystemCppRepresentation
        Holds the C++-ified representation of the system, a return object
    """
    indent = "    "
    cpp_struct_param_string = f"{indent}"
    raise Exception(f"Entry: {entry.name} | Y.FixedValueEntry not yet handled")
    return cpp_struct_param_string

def convert_parameter_entry_to_cpp_struct(
        entry : Y.ParameterEntry,
        system_name : str,
        system_cpp_representation : SystemCppRepresentation
    ) -> None:
    """
    Convert a parameter entry to C++ headers and structs.

    Parameters
    ----------
    entry : Y.ParameterEntry
        The XTCE parameter entry to convert
    system_name : str
        The name of the system to which the parameter entry belongs.
        Used to determine if the parameter entry belongs to this current system. (TODO)
    system_cpp_representation : SystemCppRepresentation
        Holds the C++-fiied representation of the system, a return object
    """
    indent = "    "
    cpp_struct_param_string = f"{indent}"
    if isinstance(entry.parameter, Y.AggregateParameter):
        # parameter_name = entry.parameter.name.replace(" ", "_")
        # aggregate_string = f"struct {parameter_name} {{\n"
        # for aggregate_member in entry.parameter.members:
        #     aggregate_string += convert_parameter_entry_to_cpp_struct(
        #         Y.ParameterEntry(aggregate_member),
        #         system_name,
        #         system_cpp_representation
        #     )
        # aggregate_string += f"}};\n\n\n"
        # aggregate_name = parameter_name
        # if aggregate_name not in system_cpp_representation.system_globals_list:
        #     system_cpp_representation.system_globals_list.append(aggregate_name)
        #     system_cpp_representation.system_globals += aggregate_string
        # cpp_struct_param_string += f"{aggregate_name} m{parameter_name};\n"
        cpp_struct_param_string += f"// AggregateParameter: {entry.parameter.name} not yet handled\n"

    elif isinstance(entry.parameter, Y.BooleanParameter):
        bits = entry.parameter.encoding.bits
        bit_field = ""
        if bits < 8:
            bit_field = f" : {bits}"
            bits = 8
        parameter_name = entry.parameter.name.replace(" ", "_")
        # Use uint8_t instead of bool to make explicit
        cpp_struct_param_string += f"uint8_t {parameter_name}{bit_field};\n"
    elif isinstance(entry.parameter, Y.EnumeratedParameter):
        if isinstance(entry.parameter.encoding, Y.IntegerEncoding):
            is_unsigned = False
            bits = entry.parameter.encoding.bits
            bit_field = ""
            if bits < 8:
                bit_field = f" : {bits}"
                bits = 8
            match entry.parameter.encoding.scheme:
                case Y.IntegerEncodingScheme.UNSIGNED:
                    is_unsigned = True
                case Y.IntegerEncodingScheme.TWOS_COMPLEMENT:
                    is_unsigned = False
                case _:
                    raise Exception(f"Y.IntegerEncodingScheme: {entry.parameter.encoding} is not supported")
            parameter_name = entry.parameter.name.replace(" ", "_")
            enum_string = f"namespace {parameter_name} {{\n"
            enum_string += f"{indent}enum type {{\n"
            for choice in entry.parameter.choices:
                if isinstance(choice, tuple):
                    enum_member_name = choice[1].replace(" ", "_")
                    enum_string += f"{indent}{indent}{enum_member_name} = {choice[0]},\n"
                elif isinstance(choice, enum.Enum):
                    enum_member_name = choice.name.replace(" ", "_")
                    enum_string += f"{indent}{indent}{enum_member_name},\n"
                else:
                    raise Exception(f"Choice: {choice} is not a tuple or enum")
            enum_string += f"{indent}}};\n}}\n\n"
            # if entry.parameter.system.name == system_name:
            #     TODO: handle case where an enum shows up that is already defined in another subsystem
            #     print(f" Enum: {enum_string}\n")
            system_cpp_representation.system_globals += enum_string
            struct_member_enum_type_name = f"{parameter_name}::type"
            cpp_struct_param_string += f"{struct_member_enum_type_name} m{parameter_name}{bit_field};\n"
        else:
            raise Exception(f"Entry: {entry.parameter.name}, system: {entry.parameter.system.name} encoding: {entry.parameter.encoding} is not supported")
    elif isinstance(entry.parameter, Y.FloatParameter) or isinstance(entry.parameter, Y.FloatMember):
        bits = entry.parameter.encoding.bits
        parameter_name = entry.parameter.name.replace(" ", "_")
        type_str = ''
        match bits:
            case 32:
                type_str = 'float'
            case 64:
                type_str = 'double'
            case _:
                raise Exception(f"{bits} bit float is not supported")
        cpp_struct_param_string += f"{type_str} {parameter_name};\n"
    elif isinstance(entry.parameter, Y.IntegerParameter):
        is_unsigned = (entry.parameter.encoding.scheme == Y.IntegerEncodingScheme.UNSIGNED)
        bits = entry.parameter.encoding.bits
        bit_field = ""
        if bits < 8:
            bit_field = f" : {bits}"
            bits = 8
        type_str = ("u" if is_unsigned else "")
        type_str += "int" + str(bits) + "_t"
        parameter_name = entry.parameter.name.replace(" ", "_")
        cpp_struct_param_string += f"{type_str} {parameter_name}{bit_field};\n"
    else:
        raise Exception(f"Entry: {entry.parameter.name} | Unexpected parameter {entry.parameter.__class__}")

    return cpp_struct_param_string

def convert_container_to_cpp_struct(
        container : Y.Container,
        system_cpp_representation : SystemCppRepresentation
    ) -> None:
    """
    Convert an XTCE container to a C++ headers and structs.

    Parameters
    ----------
    container : Y.Container
        The XTCE container to convert
    system_cpp_representation : SystemCppRepresentation
        Holds the C++-ified representation of the system, a return object
    """
    if len(container.entries) == 0:
        return

    struct_name = container.name.replace(" ", "_") + "_container"
    cpp_struct_string = f"struct __attribute__ ((__packed__)) {struct_name} {{\n"
    
    if container.extra.get("cpp_attribute_packed_struct") == "True":
        raise Exception(f"Container: {container.name} | Found a cpp_attribute_packed_struct tag equal to True. Please resolve with convert_cpp_attribute_packed_order_containers_to_network_order() first.")
    elif container.extra.get("cpp_attribute_packed_struct") == "Unresolved":
        cpp_struct_string += f"    // This struct has byte-boundary crossing issues. Please resolve with manually.\n"
        container.extra.pop("cpp_attribute_packed_struct")
    else:
        for entry in container.entries:
            if isinstance(entry, Y.ParameterEntry):
                cpp_struct_string += convert_parameter_entry_to_cpp_struct(entry, container.system.name, system_cpp_representation)
            elif isinstance(entry, Y.FixedValueEntry):
                cpp_struct_string += convert_fixed_value_entry_to_cpp_struct(entry, container.system.name, system_cpp_representation)
            else:
                raise Exception(f"Unexpected entry {entry.__class__}")
    cpp_struct_string += "};\n\n"
    system_cpp_representation.structs_definitions += cpp_struct_string
    return

def convert_to_cpp_headers(spacesystem : Y.System | Y.Subsystem) -> None:
    """
    Convert the XTCE spacesystem to C++ headers and structs.

    Parameters
    ----------
    spacesystem : Y.System | Y.Subsystem
        The XTCE spacesystem to convert
    """

    # Every subsystem outputs to a separate file
    # for system in [spacesystem, *spacesystem.subsystems]:
    for system in [*spacesystem.subsystems]:
        print(f"Converting system: {system.name} to C++ headers and structs")
        system_cpp_representation = SystemCppRepresentation()
        system_cpp_representation.includes = "#include <stdint.h>\n\n"
        system_cpp_representation.filename = system.name.replace(" ", "_") + "_containerdef.h"        
        for container in system.containers:
            convert_container_to_cpp_struct(container, system_cpp_representation)
        with open ("output/" + system_cpp_representation.filename, "w") as f:
            f.write(system_cpp_representation.dumps())
