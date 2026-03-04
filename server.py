#!/usr/bin/env python3
"""
SONiC PSU gRPC Server — mock/simulated implementation.

Exposes every method from PsuBase (and DeviceBase) over gRPC.
Simulates two PSUs, each with 1 fan and 2 thermal sensors, using
realistic default values.
"""

import logging
import random
import sys
from concurrent import futures

import grpc
import psu_service_pb2 as pb2
import psu_service_pb2_grpc as pb2_grpc

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATUS_LED_COLOR_GREEN = "green"
STATUS_LED_COLOR_AMBER = "amber"
STATUS_LED_COLOR_RED = "red"
STATUS_LED_COLOR_OFF = "off"
VALID_LED_COLORS = {
    STATUS_LED_COLOR_GREEN,
    STATUS_LED_COLOR_AMBER,
    STATUS_LED_COLOR_RED,
    STATUS_LED_COLOR_OFF,
}

DEFAULT_PORT = 50051
NUM_PSUS = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("psu_server")


# ---------------------------------------------------------------------------
# Mock PSU data model
# ---------------------------------------------------------------------------
class MockPsu:
    """Holds simulated state for a single PSU."""

    def __init__(self, index: int):
        self.index = index
        self.name = f"PSU {index + 1}"
        self.presence = True
        self.model = f"DPS-1100AB-{11 + index}"
        self.serial = f"SN{'A' if index == 0 else 'B'}{random.randint(100000, 999999)}"
        self.revision = f"A{index}"
        self.status = True
        self.replaceable = True

        # Fans — 1 per PSU
        self.fans = [f"PSU {index + 1} Fan 1"]

        # Thermals — 2 per PSU
        self.thermals = [
            f"PSU {index + 1} Temp Sensor 1",
            f"PSU {index + 1} Temp Sensor 2",
        ]

        # Electrical (output)
        self.voltage = 12.05 + index * 0.02          # V
        self.current = 14.8 + index * 0.5             # A
        self.power = round(self.voltage * self.current, 2)  # W
        self.powergood = True

        # Electrical (input — AC side)
        self.input_voltage = 220.0 + index * 1.0      # V AC
        self.input_current = 0.85 + index * 0.03       # A AC

        # Temperature
        self.temperature = 34.5 + index * 1.5           # °C
        self.temperature_high_threshold = 60.0           # °C

        # Voltage thresholds
        self.voltage_high_threshold = 13.2               # V
        self.voltage_low_threshold = 10.8                # V

        # Power thresholds / capacity
        self.max_supplied_power = 1100.0                 # W
        self.power_warning_suppress_threshold = 1050.0   # W
        self.power_critical_threshold = 1080.0           # W

        # LED
        self.status_led = STATUS_LED_COLOR_GREEN


class MockPsuPlatform:
    """Platform-level state shared across PSUs."""

    def __init__(self, num_psus: int = NUM_PSUS):
        self.psus = [MockPsu(i) for i in range(num_psus)]
        self.master_led = STATUS_LED_COLOR_GREEN

    def get_psu(self, index: int) -> MockPsu:
        if 0 <= index < len(self.psus):
            return self.psus[index]
        return None


# ---------------------------------------------------------------------------
# gRPC servicer
# ---------------------------------------------------------------------------
class PsuServiceServicer(pb2_grpc.PsuServiceServicer):

    def __init__(self, platform: MockPsuPlatform):
        self._platform = platform

    # -- helpers -------------------------------------------------------------
    def _get_psu_or_error(self, psu_index: int, context):
        """Return MockPsu or set gRPC error and return None."""
        psu = self._platform.get_psu(psu_index)
        if psu is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(
                f"PSU index {psu_index} out of range "
                f"(valid: 0–{len(self._platform.psus) - 1})"
            )
        return psu

    def _validate_led_color(self, color: str, context) -> bool:
        if color not in VALID_LED_COLORS:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                f"Invalid LED color '{color}'. "
                f"Valid: {', '.join(sorted(VALID_LED_COLORS))}"
            )
            return False
        return True

    # -- DeviceBase ----------------------------------------------------------
    def GetName(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetNameResponse()
        logger.info("GetName(psu=%d) → %s", request.psu_index, psu.name)
        return pb2.GetNameResponse(name=psu.name)

    def GetPresence(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetPresenceResponse()
        logger.info("GetPresence(psu=%d) → %s", request.psu_index, psu.presence)
        return pb2.GetPresenceResponse(presence=psu.presence)

    def GetModel(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetModelResponse()
        logger.info("GetModel(psu=%d) → %s", request.psu_index, psu.model)
        return pb2.GetModelResponse(model=psu.model)

    def GetSerial(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetSerialResponse()
        logger.info("GetSerial(psu=%d) → %s", request.psu_index, psu.serial)
        return pb2.GetSerialResponse(serial=psu.serial)

    def GetRevision(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetRevisionResponse()
        logger.info("GetRevision(psu=%d) → %s", request.psu_index, psu.revision)
        return pb2.GetRevisionResponse(revision=psu.revision)

    def GetStatus(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetStatusResponse()
        logger.info("GetStatus(psu=%d) → %s", request.psu_index, psu.status)
        return pb2.GetStatusResponse(status=psu.status)

    def GetPositionInParent(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetPositionInParentResponse()
        pos = psu.index + 1  # 1-based position
        logger.info("GetPositionInParent(psu=%d) → %d", request.psu_index, pos)
        return pb2.GetPositionInParentResponse(position=pos)

    def IsReplaceable(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.IsReplaceableResponse()
        logger.info("IsReplaceable(psu=%d) → %s", request.psu_index, psu.replaceable)
        return pb2.IsReplaceableResponse(replaceable=psu.replaceable)

    # -- PsuBase: fans -------------------------------------------------------
    def GetNumFans(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetNumFansResponse()
        n = len(psu.fans)
        logger.info("GetNumFans(psu=%d) → %d", request.psu_index, n)
        return pb2.GetNumFansResponse(num_fans=n)

    def GetAllFans(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetAllFansResponse()
        fans = [pb2.FanInfo(name=f) for f in psu.fans]
        logger.info("GetAllFans(psu=%d) → %d fans", request.psu_index, len(fans))
        return pb2.GetAllFansResponse(fans=fans)

    def GetFan(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetFanResponse()
        idx = request.fan_index
        if idx < 0 or idx >= len(psu.fans):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(
                f"Fan index {idx} out of range for PSU {request.psu_index} "
                f"(valid: 0–{len(psu.fans) - 1})"
            )
            return pb2.GetFanResponse()
        logger.info("GetFan(psu=%d, fan=%d) → %s", request.psu_index, idx, psu.fans[idx])
        return pb2.GetFanResponse(fan=pb2.FanInfo(name=psu.fans[idx]))

    # -- PsuBase: thermals ---------------------------------------------------
    def GetNumThermals(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetNumThermalsResponse()
        n = len(psu.thermals)
        logger.info("GetNumThermals(psu=%d) → %d", request.psu_index, n)
        return pb2.GetNumThermalsResponse(num_thermals=n)

    def GetAllThermals(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetAllThermalsResponse()
        thermals = [pb2.ThermalInfo(name=t) for t in psu.thermals]
        logger.info("GetAllThermals(psu=%d) → %d thermals", request.psu_index, len(thermals))
        return pb2.GetAllThermalsResponse(thermals=thermals)

    def GetThermal(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetThermalResponse()
        idx = request.thermal_index
        if idx < 0 or idx >= len(psu.thermals):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(
                f"Thermal index {idx} out of range for PSU {request.psu_index} "
                f"(valid: 0–{len(psu.thermals) - 1})"
            )
            return pb2.GetThermalResponse()
        logger.info("GetThermal(psu=%d, thermal=%d) → %s", request.psu_index, idx, psu.thermals[idx])
        return pb2.GetThermalResponse(thermal=pb2.ThermalInfo(name=psu.thermals[idx]))

    # -- PsuBase: electrical -------------------------------------------------
    def GetVoltage(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetVoltageResponse()
        logger.info("GetVoltage(psu=%d) → %.2f V", request.psu_index, psu.voltage)
        return pb2.GetVoltageResponse(voltage=psu.voltage)

    def GetCurrent(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetCurrentResponse()
        logger.info("GetCurrent(psu=%d) → %.2f A", request.psu_index, psu.current)
        return pb2.GetCurrentResponse(current=psu.current)

    def GetPower(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetPowerResponse()
        logger.info("GetPower(psu=%d) → %.2f W", request.psu_index, psu.power)
        return pb2.GetPowerResponse(power=psu.power)

    def GetPowergoodStatus(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetPowergoodStatusResponse()
        logger.info("GetPowergoodStatus(psu=%d) → %s", request.psu_index, psu.powergood)
        return pb2.GetPowergoodStatusResponse(powergood=psu.powergood)

    def GetInputVoltage(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetInputVoltageResponse()
        logger.info("GetInputVoltage(psu=%d) → %.2f V", request.psu_index, psu.input_voltage)
        return pb2.GetInputVoltageResponse(voltage=psu.input_voltage)

    def GetInputCurrent(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetInputCurrentResponse()
        logger.info("GetInputCurrent(psu=%d) → %.2f A", request.psu_index, psu.input_current)
        return pb2.GetInputCurrentResponse(current=psu.input_current)

    # -- PsuBase: LEDs -------------------------------------------------------
    def SetStatusLed(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.SetStatusLedResponse()
        if not self._validate_led_color(request.color, context):
            return pb2.SetStatusLedResponse(success=False)
        psu.status_led = request.color
        logger.info("SetStatusLed(psu=%d, color=%s) → True", request.psu_index, request.color)
        return pb2.SetStatusLedResponse(success=True)

    def GetStatusLed(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetStatusLedResponse()
        logger.info("GetStatusLed(psu=%d) → %s", request.psu_index, psu.status_led)
        return pb2.GetStatusLedResponse(color=psu.status_led)

    def GetStatusMasterLed(self, request, context):
        color = self._platform.master_led
        logger.info("GetStatusMasterLed() → %s", color)
        return pb2.GetStatusMasterLedResponse(color=color)

    def SetStatusMasterLed(self, request, context):
        if not self._validate_led_color(request.color, context):
            return pb2.SetStatusMasterLedResponse(success=False)
        self._platform.master_led = request.color
        logger.info("SetStatusMasterLed(color=%s) → True", request.color)
        return pb2.SetStatusMasterLedResponse(success=True)

    # -- PsuBase: temperature & thresholds -----------------------------------
    def GetTemperature(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetTemperatureResponse()
        logger.info("GetTemperature(psu=%d) → %.1f °C", request.psu_index, psu.temperature)
        return pb2.GetTemperatureResponse(temperature=psu.temperature)

    def GetTemperatureHighThreshold(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetTemperatureHighThresholdResponse()
        logger.info("GetTemperatureHighThreshold(psu=%d) → %.1f °C", request.psu_index, psu.temperature_high_threshold)
        return pb2.GetTemperatureHighThresholdResponse(threshold=psu.temperature_high_threshold)

    def GetVoltageHighThreshold(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetVoltageHighThresholdResponse()
        logger.info("GetVoltageHighThreshold(psu=%d) → %.2f V", request.psu_index, psu.voltage_high_threshold)
        return pb2.GetVoltageHighThresholdResponse(threshold=psu.voltage_high_threshold)

    def GetVoltageLowThreshold(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetVoltageLowThresholdResponse()
        logger.info("GetVoltageLowThreshold(psu=%d) → %.2f V", request.psu_index, psu.voltage_low_threshold)
        return pb2.GetVoltageLowThresholdResponse(threshold=psu.voltage_low_threshold)

    def GetMaximumSuppliedPower(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetMaximumSuppliedPowerResponse()
        logger.info("GetMaximumSuppliedPower(psu=%d) → %.1f W", request.psu_index, psu.max_supplied_power)
        return pb2.GetMaximumSuppliedPowerResponse(power=psu.max_supplied_power)

    def GetPsuPowerWarningSuppressThreshold(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetPsuPowerWarningSuppressThresholdResponse()
        logger.info("GetPsuPowerWarningSuppressThreshold(psu=%d) → %.1f W", request.psu_index, psu.power_warning_suppress_threshold)
        return pb2.GetPsuPowerWarningSuppressThresholdResponse(threshold=psu.power_warning_suppress_threshold)

    def GetPsuPowerCriticalThreshold(self, request, context):
        psu = self._get_psu_or_error(request.psu_index, context)
        if psu is None:
            return pb2.GetPsuPowerCriticalThresholdResponse()
        logger.info("GetPsuPowerCriticalThreshold(psu=%d) → %.1f W", request.psu_index, psu.power_critical_threshold)
        return pb2.GetPsuPowerCriticalThresholdResponse(threshold=psu.power_critical_threshold)


# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------
def serve(port: int = DEFAULT_PORT, num_psus: int = NUM_PSUS):
    platform = MockPsuPlatform(num_psus)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_PsuServiceServicer_to_server(PsuServiceServicer(platform), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("PSU gRPC server started on port %d with %d simulated PSU(s)", port, num_psus)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down…")
        server.stop(grace=2).wait()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SONiC PSU gRPC Server (mock)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Listen port")
    parser.add_argument("--num-psus", type=int, default=NUM_PSUS, help="Number of simulated PSUs")
    args = parser.parse_args()
    serve(port=args.port, num_psus=args.num_psus)
