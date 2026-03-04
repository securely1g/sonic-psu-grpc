#!/usr/bin/env python3
"""
SONiC PSU gRPC Test Client

Connects to the PSU gRPC server and exercises every single RPC,
printing results in a readable format.
"""

import sys

import grpc
import psu_service_pb2 as pb2
import psu_service_pb2_grpc as pb2_grpc

SEPARATOR = "─" * 60


def call_rpc(label, fn, *args, **kwargs):
    """Call an RPC and print the result, handling errors."""
    try:
        resp = fn(*args, **kwargs)
        print(f"  {label}: {resp}")
    except grpc.RpcError as e:
        print(f"  {label}: ERROR [{e.code().name}] {e.details()}")


def run(host: str = "localhost:50051"):
    channel = grpc.insecure_channel(host)
    stub = pb2_grpc.PsuServiceStub(channel)

    # ── Test each PSU (0 and 1) ──────────────────────────────────────────
    for psu_idx in range(2):
        print(f"\n{'═' * 60}")
        print(f"  PSU {psu_idx}")
        print(f"{'═' * 60}")

        # DeviceBase methods
        print(f"\n{SEPARATOR}")
        print("  DeviceBase Methods")
        print(SEPARATOR)
        call_rpc("get_name",
                 stub.GetName, pb2.GetNameRequest(psu_index=psu_idx))
        call_rpc("get_presence",
                 stub.GetPresence, pb2.GetPresenceRequest(psu_index=psu_idx))
        call_rpc("get_model",
                 stub.GetModel, pb2.GetModelRequest(psu_index=psu_idx))
        call_rpc("get_serial",
                 stub.GetSerial, pb2.GetSerialRequest(psu_index=psu_idx))
        call_rpc("get_revision",
                 stub.GetRevision, pb2.GetRevisionRequest(psu_index=psu_idx))
        call_rpc("get_status",
                 stub.GetStatus, pb2.GetStatusRequest(psu_index=psu_idx))
        call_rpc("get_position_in_parent",
                 stub.GetPositionInParent, pb2.GetPositionInParentRequest(psu_index=psu_idx))
        call_rpc("is_replaceable",
                 stub.IsReplaceable, pb2.IsReplaceableRequest(psu_index=psu_idx))

        # Fans
        print(f"\n{SEPARATOR}")
        print("  Fan Methods")
        print(SEPARATOR)
        call_rpc("get_num_fans",
                 stub.GetNumFans, pb2.GetNumFansRequest(psu_index=psu_idx))
        call_rpc("get_all_fans",
                 stub.GetAllFans, pb2.GetAllFansRequest(psu_index=psu_idx))
        call_rpc("get_fan(0)",
                 stub.GetFan, pb2.GetFanRequest(psu_index=psu_idx, fan_index=0))
        # Invalid fan index — should return error
        call_rpc("get_fan(99) [expect error]",
                 stub.GetFan, pb2.GetFanRequest(psu_index=psu_idx, fan_index=99))

        # Thermals
        print(f"\n{SEPARATOR}")
        print("  Thermal Methods")
        print(SEPARATOR)
        call_rpc("get_num_thermals",
                 stub.GetNumThermals, pb2.GetNumThermalsRequest(psu_index=psu_idx))
        call_rpc("get_all_thermals",
                 stub.GetAllThermals, pb2.GetAllThermalsRequest(psu_index=psu_idx))
        call_rpc("get_thermal(0)",
                 stub.GetThermal, pb2.GetThermalRequest(psu_index=psu_idx, thermal_index=0))
        call_rpc("get_thermal(1)",
                 stub.GetThermal, pb2.GetThermalRequest(psu_index=psu_idx, thermal_index=1))
        # Invalid thermal index
        call_rpc("get_thermal(99) [expect error]",
                 stub.GetThermal, pb2.GetThermalRequest(psu_index=psu_idx, thermal_index=99))

        # Electrical (output)
        print(f"\n{SEPARATOR}")
        print("  Electrical (Output)")
        print(SEPARATOR)
        call_rpc("get_voltage",
                 stub.GetVoltage, pb2.GetVoltageRequest(psu_index=psu_idx))
        call_rpc("get_current",
                 stub.GetCurrent, pb2.GetCurrentRequest(psu_index=psu_idx))
        call_rpc("get_power",
                 stub.GetPower, pb2.GetPowerRequest(psu_index=psu_idx))
        call_rpc("get_powergood_status",
                 stub.GetPowergoodStatus, pb2.GetPowergoodStatusRequest(psu_index=psu_idx))

        # Electrical (input)
        print(f"\n{SEPARATOR}")
        print("  Electrical (Input)")
        print(SEPARATOR)
        call_rpc("get_input_voltage",
                 stub.GetInputVoltage, pb2.GetInputVoltageRequest(psu_index=psu_idx))
        call_rpc("get_input_current",
                 stub.GetInputCurrent, pb2.GetInputCurrentRequest(psu_index=psu_idx))

        # Temperature & thresholds
        print(f"\n{SEPARATOR}")
        print("  Temperature & Thresholds")
        print(SEPARATOR)
        call_rpc("get_temperature",
                 stub.GetTemperature, pb2.GetTemperatureRequest(psu_index=psu_idx))
        call_rpc("get_temperature_high_threshold",
                 stub.GetTemperatureHighThreshold,
                 pb2.GetTemperatureHighThresholdRequest(psu_index=psu_idx))
        call_rpc("get_voltage_high_threshold",
                 stub.GetVoltageHighThreshold,
                 pb2.GetVoltageHighThresholdRequest(psu_index=psu_idx))
        call_rpc("get_voltage_low_threshold",
                 stub.GetVoltageLowThreshold,
                 pb2.GetVoltageLowThresholdRequest(psu_index=psu_idx))
        call_rpc("get_maximum_supplied_power",
                 stub.GetMaximumSuppliedPower,
                 pb2.GetMaximumSuppliedPowerRequest(psu_index=psu_idx))
        call_rpc("get_psu_power_warning_suppress_threshold",
                 stub.GetPsuPowerWarningSuppressThreshold,
                 pb2.GetPsuPowerWarningSuppressThresholdRequest(psu_index=psu_idx))
        call_rpc("get_psu_power_critical_threshold",
                 stub.GetPsuPowerCriticalThreshold,
                 pb2.GetPsuPowerCriticalThresholdRequest(psu_index=psu_idx))

        # Status LED
        print(f"\n{SEPARATOR}")
        print("  Status LED")
        print(SEPARATOR)
        call_rpc("get_status_led",
                 stub.GetStatusLed, pb2.GetStatusLedRequest(psu_index=psu_idx))
        call_rpc("set_status_led('amber')",
                 stub.SetStatusLed,
                 pb2.SetStatusLedRequest(psu_index=psu_idx, color="amber"))
        call_rpc("get_status_led (after set)",
                 stub.GetStatusLed, pb2.GetStatusLedRequest(psu_index=psu_idx))
        # Invalid color
        call_rpc("set_status_led('purple') [expect error]",
                 stub.SetStatusLed,
                 pb2.SetStatusLedRequest(psu_index=psu_idx, color="purple"))

    # ── Master LED (class-level) ─────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print("  Master LED (class-level)")
    print(f"{'═' * 60}")
    call_rpc("get_status_master_led",
             stub.GetStatusMasterLed, pb2.GetStatusMasterLedRequest())
    call_rpc("set_status_master_led('red')",
             stub.SetStatusMasterLed, pb2.SetStatusMasterLedRequest(color="red"))
    call_rpc("get_status_master_led (after set)",
             stub.GetStatusMasterLed, pb2.GetStatusMasterLedRequest())
    # Invalid color
    call_rpc("set_status_master_led('blue') [expect error]",
             stub.SetStatusMasterLed, pb2.SetStatusMasterLedRequest(color="blue"))

    # ── Invalid PSU index ────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print("  Error Handling — Invalid PSU Index")
    print(f"{'═' * 60}")
    call_rpc("get_name(psu=99) [expect error]",
             stub.GetName, pb2.GetNameRequest(psu_index=99))

    print(f"\n{'═' * 60}")
    print("  All RPCs tested ✓")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost:50051"
    run(host)
