#!/usr/bin/env bash
# generate_proto.sh — Generate Python gRPC stubs from psu_service.proto
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Generating Python gRPC code from psu_service.proto …"
python3 -m grpc_tools.protoc \
    -I"${SCRIPT_DIR}" \
    --python_out="${SCRIPT_DIR}" \
    --grpc_python_out="${SCRIPT_DIR}" \
    "${SCRIPT_DIR}/psu_service.proto"

echo "Generated:"
ls -1 "${SCRIPT_DIR}"/psu_service_pb2*.py
echo "Done ✓"
