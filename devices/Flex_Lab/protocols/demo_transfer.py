"""
Demo transfer protocol for Opentrons Flex choreography demos.

Matches a typical Chemelian deck layout:
  - tip rack in B2
  - 96-well plate in C2 (override with plate_slot)
  - trash bin in A3
  - Flex 50 uL single-channel pipette on the right mount

Runtime parameters let the control script choose slot, wells, and volume
without rewriting this file for each demo step.
"""

from opentrons import protocol_api

metadata = {
    "protocolName": "Flex Lab Demo Transfer",
    "author": "Flex Lab control layer",
    "description": "Parameterized aspirate/dispense for demo choreography.",
}

requirements = {"robotType": "Flex", "apiLevel": "2.20"}


def add_parameters(parameters: protocol_api.ParameterContext) -> None:
    slots = [
        {"display_name": slot, "value": slot}
        for slot in ("A1", "A2", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "D3")
    ]
    wells = [
        {"display_name": f"{row}{col}", "value": f"{row}{col}"}
        for col in range(1, 13)
        for row in "ABCDEFGH"
    ]

    parameters.add_str(
        variable_name="plate_slot",
        display_name="Plate deck slot",
        description="Deck slot holding the destination/source 96-well plate.",
        choices=slots,
        default="C2",
    )
    parameters.add_str(
        variable_name="tiprack_slot",
        display_name="Tip rack slot",
        description="Deck slot holding the 50 uL tip rack.",
        choices=slots,
        default="B2",
    )
    parameters.add_str(
        variable_name="source_well",
        display_name="Source well",
        description="Well to aspirate from.",
        choices=wells,
        default="A1",
    )
    parameters.add_str(
        variable_name="dest_well",
        display_name="Destination well",
        description="Well to dispense into.",
        choices=wells,
        default="B1",
    )
    parameters.add_float(
        variable_name="volume_ul",
        display_name="Volume",
        description="Transfer volume in microliters.",
        default=10.0,
        minimum=5.0,
        maximum=50.0,
        unit="µL",
    )


def run(protocol: protocol_api.ProtocolContext) -> None:
    plate_slot = protocol.params.plate_slot
    tiprack_slot = protocol.params.tiprack_slot
    source_well = protocol.params.source_well
    dest_well = protocol.params.dest_well
    volume_ul = float(protocol.params.volume_ul)

    tiprack = protocol.load_labware(
        "opentrons_flex_96_tiprack_50ul", tiprack_slot
    )
    plate = protocol.load_labware(
        "opentrons_96_wellplate_200ul_pcr_full_skirt", plate_slot
    )
    trash = protocol.load_trash_bin("A3")

    pipette = protocol.load_instrument(
        "flex_1channel_50",
        mount="right",
        tip_racks=[tiprack],
    )

    protocol.comment(
        f"Transfer {volume_ul} uL from {plate_slot}/{source_well} "
        f"to {plate_slot}/{dest_well}"
    )

    pipette.pick_up_tip()
    pipette.aspirate(volume_ul, plate[source_well])
    pipette.dispense(volume_ul, plate[dest_well])
    pipette.drop_tip(trash)
