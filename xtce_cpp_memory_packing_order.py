from __future__ import annotations

import yamcs.pymdb as Y
from .constants import CPP_ATTRIBUTE_PACKED_STRUCT

def convert_container_to_cpp_struct(
        container : Y.Container
    ) -> None:
    """
    Convert containers described in a C++ memory-packed order to the order
    it will be received over the network.
    Modifications to the container are made in-place.

    Parameters
    ----------
    spacesystem : Y.System | Y.Subsystem
        The XTCE spacesystem to modify
    """
    if not CPP_ATTRIBUTE_PACKED_STRUCT in container.extra:
        return
    elif container.extra.get(CPP_ATTRIBUTE_PACKED_STRUCT) != "True":
        raise Exception(f"Container: {container.name} | cpp_attribute_packed_struct must be True! Got: {container.extra.get('cpp_attribute_packed_struct')}")
    container.extra.pop(CPP_ATTRIBUTE_PACKED_STRUCT)
    # Iterate over all entries, see if it is a multiple of 8
    # Re-ordered entries will be stored here
    reordered_entries = []
    # Temporary holder for each byte
    reordered_byte = []
    # Have a running sum of the bits, they must add to exactly 8 or else there will be a byte-boundary crossing
    bit_count = 0
    for entry in container.entries:
        if isinstance(entry, Y.ParameterEntry):
            if isinstance(entry.parameter, Y.IntegerParameter):
                # Check if the encoding is a multiple of 8
                bits = entry.parameter.encoding.bits
                bit_count += bits
                reordered_byte.insert(0, entry)
                # A bitfield that crosses byte-boundaries is not supported,
                # but a single uint8_t, uint16_t, uint32_t, etc. is supported
                if bit_count > 8 and len(reordered_byte) > 1:
                    container.extra[CPP_ATTRIBUTE_PACKED_STRUCT] = "Unresolved"
                    print(f"Warning, detected a byte-boundary crossing in Container: {container.name}. Marking as Unresolved.")
                    return
                elif bit_count % 8 == 0:
                    # Properly byte-aligned, add the reordered byte to the list
                    reordered_entries.extend(reordered_byte)
                    reordered_byte = []
                    bit_count = 0
            else:
                raise Exception(f"Container: {container.name} | Entry: {entry.parameter.name} | Encoding: {entry.parameter.encoding} is not supported")
        else:
            raise Exception(f"Container: {container.name} | Entry: {entry.__class__} is not supported")
    # Handle an unfilled byte, if any
    # TODO: Might need to add reserved padding to pad out to 8 bits?
    if bit_count > 0:
        reordered_entries.extend(reordered_byte)
    # Update the entries to the reordered entries
    container.entries = reordered_entries

def convert_cpp_attribute_packed_order_containers_to_network_order(spacesystem : Y.System | Y.Subsystem) -> None:
    """
    Convert containers in the spacesystem described in a C++ memory-packed order
    to the order it will be received over the network.
    Specifically, this function looks for containers that have the
    cpp_attribute_packed_struct key in extras set to True.
    The key will be removed if successfully processed or changed to Unresolved.
    Modifications to the XTCE spacesystem are made in-place.

    Parameters
    ----------
    spacesystem : Y.System | Y.Subsystem
        The XTCE spacesystem to modify
    """

    # Every subsystem outputs to a separate file
    for system in [spacesystem, *spacesystem.subsystems]:
        for container in system.containers:
            convert_container_to_cpp_struct(container)
