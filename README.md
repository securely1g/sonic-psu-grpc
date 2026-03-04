# SONiC PSU gRPC Service

A self-contained Python gRPC server that exposes **all** methods from SONiC's
`PsuBase` class (and its parent `DeviceBase`) over gRPC.

Includes a mock/simulated implementation with 2 PSUs, each with 1 fan and
2 thermal sensors, using realistic default values.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate Python protobuf/gRPC code
bash generate_proto.sh

# 3. Start the server (terminal 1)
python3 server.py

# 4. Run the test client (terminal 2)
python3 client.py
```

## Project Structure

| File | Description |
|---|---|
| `psu_service.proto` | Protobuf / gRPC service definition (proto3, package `sonic.psu.v1`) |
| `server.py` | gRPC server with mock PSU implementation |
| `client.py` | Test client that exercises every RPC |
| `generate_proto.sh` | Generates `psu_service_pb2.py` and `psu_service_pb2_grpc.py` |
| `requirements.txt` | Python dependencies |

## RPC Reference

### DeviceBase Methods

All take a `psu_index` (int32) to select the target PSU.

| RPC | Returns |
|---|---|
| `GetName` | string name |
| `GetPresence` | bool |
| `GetModel` | string |
| `GetSerial` | string |
| `GetRevision` | string |
| `GetStatus` | bool |
| `GetPositionInParent` | int32 |
| `IsReplaceable` | bool |

### PsuBase Methods — Fans & Thermals

| RPC | Returns |
|---|---|
| `GetNumFans` | int32 |
| `GetAllFans` | repeated `FanInfo` |
| `GetFan` | `FanInfo` (takes `fan_index`) |
| `GetNumThermals` | int32 |
| `GetAllThermals` | repeated `ThermalInfo` |
| `GetThermal` | `ThermalInfo` (takes `thermal_index`) |

### PsuBase Methods — Electrical

| RPC | Returns |
|---|---|
| `GetVoltage` | float (output DC voltage, ~12 V) |
| `GetCurrent` | float (output DC current, ~15 A) |
| `GetPower` | float (output power, W) |
| `GetPowergoodStatus` | bool |
| `GetInputVoltage` | float (input AC voltage, ~220 V) |
| `GetInputCurrent` | float (input AC current, ~0.85 A) |

### PsuBase Methods — Temperature & Thresholds

| RPC | Returns |
|---|---|
| `GetTemperature` | float (°C) |
| `GetTemperatureHighThreshold` | float (°C) |
| `GetVoltageHighThreshold` | float (V) |
| `GetVoltageLowThreshold` | float (V) |
| `GetMaximumSuppliedPower` | float (W) |
| `GetPsuPowerWarningSuppressThreshold` | float (W) |
| `GetPsuPowerCriticalThreshold` | float (W) |

### PsuBase Methods — Status LEDs

| RPC | Returns |
|---|---|
| `GetStatusLed` | string (color) |
| `SetStatusLed` | bool (takes `color`: green/amber/red/off) |
| `GetStatusMasterLed` | string (class-level, no `psu_index`) |
| `SetStatusMasterLed` | bool (class-level, takes `color`) |

## Server Options

```bash
python3 server.py --port 50051 --num-psus 4
```

| Flag | Default | Description |
|---|---|---|
| `--port` | `50051` | gRPC listen port |
| `--num-psus` | `2` | Number of simulated PSUs |

## Error Handling

The server returns proper gRPC status codes:

- **`NOT_FOUND`** — invalid `psu_index`, `fan_index`, or `thermal_index`
- **`INVALID_ARGUMENT`** — invalid LED color string

The test client demonstrates these error cases explicitly.

## Mock PSU Default Values

| Parameter | PSU 0 | PSU 1 |
|---|---|---|
| Model | DPS-1100AB-11 | DPS-1100AB-12 |
| Output Voltage | 12.05 V | 12.07 V |
| Output Current | 14.80 A | 15.30 A |
| Input Voltage | 220.0 V | 221.0 V |
| Temperature | 34.5 °C | 36.0 °C |
| Max Power | 1100 W | 1100 W |
| Fans | 1 | 1 |
| Thermals | 2 | 2 |
