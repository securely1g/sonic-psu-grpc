# SONiC PSU gRPC — Rust Client

A Rust client that exercises **all 29 RPCs** of the SONiC PSU gRPC service.

## Prerequisites

- **Rust toolchain** (1.70+): <https://rustup.rs>
- **protoc** (protobuf compiler):
  ```bash
  # Ubuntu/Debian
  sudo apt-get install -y protobuf-compiler

  # macOS
  brew install protobuf
  ```
- The Python gRPC server running (see parent directory's README)

## Build & Run

```bash
# Start the Python server first (from parent directory)
cd .. && python3 server.py &

# Build the Rust client
cargo build --release

# Run it
cargo run --release

# Or with options
cargo run --release -- --addr http://127.0.0.1:50051 --num-psus 4
```

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `-a, --addr` | `http://127.0.0.1:50051` | gRPC server address |
| `-n, --num-psus` | `2` | Number of PSUs to query |

## What It Tests

The client calls every RPC in the service:

- **8** DeviceBase methods (name, presence, model, serial, revision, status, position, replaceable)
- **6** Fan/Thermal methods with error cases for invalid indices
- **6** Electrical methods (output + input voltage/current/power)
- **7** Temperature & threshold methods
- **4** LED methods (per-PSU + class-level master LED)
- **Error handling** — invalid PSU index, fan index, thermal index, LED color

## Project Structure

```
rust-client/
├── Cargo.toml          # Dependencies (tonic, prost, tokio, clap)
├── build.rs            # Proto compilation via tonic-build
├── proto/
│   └── psu_service.proto   # Copied from parent project
├── src/
│   └── main.rs         # Client implementation
└── README.md
```

## Dependencies

| Crate | Purpose |
|---|---|
| `tonic` | gRPC client framework |
| `prost` | Protobuf message types |
| `tokio` | Async runtime |
| `clap` | CLI argument parsing |
| `tonic-build` | Proto → Rust codegen (build-time) |
