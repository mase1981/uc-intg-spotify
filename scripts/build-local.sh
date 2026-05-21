#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VER="${PYTHON_VER:-3.11.12-0.3.0}"
BUILD_PLATFORM="${BUILD_PLATFORM:-linux/arm64}"
ARCHIVE_ARCH="${ARCHIVE_ARCH:-aarch64}"

usage() {
  cat <<USAGE
Usage: $0 [version]

Build the integration locally with the same PyInstaller image used by CI and
create an uploadable tarball.

Environment overrides:
  VERSION         Release version. Defaults to driver.json .version.
  PYTHON_VER      r2-pyinstaller tag. Defaults to ${PYTHON_VER}.
  BUILD_PLATFORM  Docker platform. Defaults to ${BUILD_PLATFORM}.
  ARCHIVE_ARCH    Artifact architecture suffix. Defaults to ${ARCHIVE_ARCH}.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command docker
require_command tar

json_value() {
  local key="$1"

  if command -v jq >/dev/null 2>&1; then
    jq -r ".${key}" driver.json
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json, sys; print(json.load(open("driver.json"))[sys.argv[1]])' "$key"
  else
    echo "Missing required command: jq or python3" >&2
    exit 1
  fi
}

cd "$ROOT_DIR"

VERSION="${VERSION:-${1:-$(json_value version)}}"
DRIVER_BASE="$(json_value driver_id | sed 's/^uc-intg-//')"
IMAGE="docker.io/unfoldedcircle/r2-pyinstaller:${PYTHON_VER}"
ARTIFACT_NAME="uc-intg-${DRIVER_BASE}-${VERSION}-${ARCHIVE_ARCH}"

if [[ -z "$VERSION" || "$VERSION" == "null" ]]; then
  echo "Could not determine version. Set VERSION or pass it as the first argument." >&2
  exit 1
fi

if [[ -z "$DRIVER_BASE" || "$DRIVER_BASE" == "null" ]]; then
  echo "Could not determine driver_id from driver.json." >&2
  exit 1
fi

if [[ "$(uname -s)" == "Linux" ]]; then
  echo "Registering qemu handlers for cross-platform Docker builds..."
  docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
fi

echo "Building intg-${DRIVER_BASE} with ${IMAGE} for ${BUILD_PLATFORM}..."
rm -rf artifacts "dist/intg-${DRIVER_BASE}" "${ARTIFACT_NAME}.tar.gz" "intg-${DRIVER_BASE}.spec"

docker run --rm --name "builder-${DRIVER_BASE}-$$" \
  --platform="${BUILD_PLATFORM}" \
  --user="$(id -u):$(id -g)" \
  -v "${ROOT_DIR}:/workspace" \
  "${IMAGE}" \
  bash -c "cd /workspace && \
    python -m pip install -r requirements.txt && \
    pyinstaller --clean --onedir --name intg-${DRIVER_BASE} --collect-all zeroconf uc_intg_spotify/driver.py"

mkdir -p artifacts/bin
mv "dist/intg-${DRIVER_BASE}"/* artifacts/bin
mv "artifacts/bin/intg-${DRIVER_BASE}" artifacts/bin/driver
cp driver.json artifacts/

tar czvf "${ARTIFACT_NAME}.tar.gz" -C "${ROOT_DIR}/artifacts" .
rm -f "intg-${DRIVER_BASE}.spec"

echo
echo "Created ${ROOT_DIR}/${ARTIFACT_NAME}.tar.gz"
