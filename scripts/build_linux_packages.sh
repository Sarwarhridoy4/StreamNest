#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="StreamNest"
PACKAGE_NAME="streamnest"
EXECUTABLE="streamnest"
DESCRIPTION="Desktop media downloader built with Flet and yt-dlp"
MAINTAINER="${MAINTAINER:-StreamNest Team <support@streamnest.app>}"
VERSION="${1:-1.0.0}"
ARCH="${2:-amd64}"

ICON_BASE="$ROOT_DIR/assets/icon"
OUT_DIR="$ROOT_DIR/dist"
DEFAULT_LINUX_OUT="$ROOT_DIR/build/linux"
FLET_FLUTTER_BUNDLE="$ROOT_DIR/build/flutter/build/linux/x64/release/bundle"
FLET_BIN=""

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command '$cmd' is not installed or not in PATH." >&2
    exit 1
  fi
}

ensure_linux_linker() {
  local llvm_bin="/usr/lib/llvm-20/bin"
  if [[ -d "$llvm_bin" ]]; then
    export PATH="$llvm_bin:$PATH"
    if [[ ! -x "$llvm_bin/ld.lld" && ! -x "$llvm_bin/ld" ]]; then
      echo "Error: Flutter Linux build requires ld.lld or ld in $llvm_bin." >&2
      echo "Install linker tools first (Ubuntu example): sudo apt install lld-20" >&2
      exit 1
    fi
  fi

  if ! command -v ld.lld >/dev/null 2>&1 && ! command -v ld >/dev/null 2>&1; then
    echo "Error: no usable linker found (ld.lld or ld)." >&2
    exit 1
  fi
}

run_flet_linux_build() {
  echo "Running official build command: $FLET_BIN build --yes linux"
  if "$FLET_BIN" build --yes --no-rich-output linux "$ROOT_DIR"; then
    return
  fi

  echo "Initial build failed. Retrying once with --clear-cache..."
  "$FLET_BIN" build --yes --no-rich-output --clear-cache linux "$ROOT_DIR"
}

resolve_bundle_dir() {
  if [[ -x "$DEFAULT_LINUX_OUT/$EXECUTABLE" ]]; then
    echo "$DEFAULT_LINUX_OUT"
    return 0
  fi

  if [[ -x "$FLET_FLUTTER_BUNDLE/$EXECUTABLE" ]]; then
    echo "$FLET_FLUTTER_BUNDLE"
    return 0
  fi

  local match
  match="$(find "$ROOT_DIR/build" -type f -name "$EXECUTABLE" -perm -111 2>/dev/null | head -n1 || true)"
  if [[ -n "$match" ]]; then
    dirname "$match"
    return 0
  fi

  return 1
}

require_command dpkg-deb
require_command desktop-file-validate
require_command appimagetool

if command -v flet >/dev/null 2>&1; then
  FLET_BIN="flet"
elif [[ -x "$ROOT_DIR/.venv/bin/flet" ]]; then
  FLET_BIN="$ROOT_DIR/.venv/bin/flet"
else
  echo "Error: 'flet' not found in PATH and '$ROOT_DIR/.venv/bin/flet' does not exist." >&2
  exit 1
fi

ensure_linux_linker
run_flet_linux_build

if ! BUILD_DIR="$(resolve_bundle_dir)"; then
  echo "Error: built Linux bundle not found after 'flet build --yes linux'." >&2
  echo "Looked for executable '$EXECUTABLE' under '$ROOT_DIR/build'." >&2
  exit 1
fi

echo "Using Linux bundle: $BUILD_DIR"

if [[ ! -f "${ICON_BASE}.png" ]]; then
  echo "Error: ${ICON_BASE}.png was not found." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

create_desktop_file() {
  local target="$1"
  local exec_cmd="$2"
  cat > "$target" <<DESKTOP
[Desktop Entry]
Name=$APP_NAME
Comment=$DESCRIPTION
Exec=$exec_cmd
Icon=$PACKAGE_NAME
Terminal=false
Type=Application
Categories=AudioVideo;
StartupNotify=true
StartupWMClass=$APP_NAME
DESKTOP
}

install_icons() {
  local root="$1"
  for size in 64 128 256 512; do
    local src="${ICON_BASE}-${size}.png"
    if [[ ! -f "$src" ]]; then
      src="${ICON_BASE}.png"
    fi
    install -Dm644 "$src" "$root/usr/share/icons/hicolor/${size}x${size}/apps/${PACKAGE_NAME}.png"
  done
}

# -----------------------------
# Build .deb package
# -----------------------------
DEB_ROOT="$WORK_DIR/deb"
mkdir -p "$DEB_ROOT/DEBIAN" "$DEB_ROOT/opt/$PACKAGE_NAME" "$DEB_ROOT/usr/bin" "$DEB_ROOT/usr/share/applications"
cp -a "$BUILD_DIR/." "$DEB_ROOT/opt/$PACKAGE_NAME/"
ln -sf "/opt/$PACKAGE_NAME/$EXECUTABLE" "$DEB_ROOT/usr/bin/$EXECUTABLE"
create_desktop_file "$DEB_ROOT/usr/share/applications/${PACKAGE_NAME}.desktop" "/opt/$PACKAGE_NAME/$EXECUTABLE"
install_icons "$DEB_ROOT"

desktop-file-validate "$DEB_ROOT/usr/share/applications/${PACKAGE_NAME}.desktop"

INSTALLED_SIZE="$(du -sk "$DEB_ROOT" | awk '{print $1}')"
cat > "$DEB_ROOT/DEBIAN/control" <<CONTROL
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Depends: libgtk-3-0, libstdc++6, libgcc-s1, libglib2.0-0
Installed-Size: $INSTALLED_SIZE
Description: $DESCRIPTION
CONTROL

DEB_OUT="$OUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$DEB_ROOT" "$DEB_OUT" >/dev/null

# -----------------------------
# Build .AppImage
# -----------------------------
APPDIR="$WORK_DIR/AppDir"
APP_USR_DIR="$APPDIR/usr"
APP_LIB_DIR="$APP_USR_DIR/lib/$PACKAGE_NAME"
mkdir -p "$APP_LIB_DIR" "$APP_USR_DIR/bin" "$APP_USR_DIR/share/applications"
cp -a "$BUILD_DIR/." "$APP_LIB_DIR/"
ln -sf "../lib/$PACKAGE_NAME/$EXECUTABLE" "$APP_USR_DIR/bin/$EXECUTABLE"

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -e
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/streamnest/streamnest" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

create_desktop_file "$APPDIR/${PACKAGE_NAME}.desktop" "$EXECUTABLE"
cp "$APPDIR/${PACKAGE_NAME}.desktop" "$APP_USR_DIR/share/applications/${PACKAGE_NAME}.desktop"
install -Dm644 "${ICON_BASE}.png" "$APPDIR/${PACKAGE_NAME}.png"
install_icons "$APPDIR"

desktop-file-validate "$APPDIR/${PACKAGE_NAME}.desktop"

APPIMAGE_ARCH="$ARCH"
case "$ARCH" in
  amd64) APPIMAGE_ARCH="x86_64" ;;
  arm64) APPIMAGE_ARCH="aarch64" ;;
esac

APPIMAGE_OUT="$OUT_DIR/${APP_NAME}-${VERSION}-${APPIMAGE_ARCH}.AppImage"
APPIMAGE_EXTRACT_AND_RUN=1 ARCH="$APPIMAGE_ARCH" appimagetool --no-appstream "$APPDIR" "$APPIMAGE_OUT" >/dev/null
chmod +x "$APPIMAGE_OUT"

(
  cd "$OUT_DIR"
  sha256sum "$(basename "$DEB_OUT")" "$(basename "$APPIMAGE_OUT")" > "checksums-${VERSION}.sha256"
)

echo "Created:"
echo "  $DEB_OUT"
echo "  $APPIMAGE_OUT"
echo "  $OUT_DIR/checksums-${VERSION}.sha256"
