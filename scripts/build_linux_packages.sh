#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="StreamNest"
PACKAGE_NAME="streamnest"
EXECUTABLE="streamnest"
DESCRIPTION="Desktop media downloader built with Flet and yt-dlp"
MAINTAINER="${MAINTAINER:-StreamNest Team <support@streamnest.app>}"
VERSION="2.0.0"
ARCH="amd64"
VERBOSE=0

ICON_BASE="$ROOT_DIR/assets/icon"
OUT_DIR="$ROOT_DIR/dist"
DEFAULT_LINUX_OUT="$ROOT_DIR/build/linux"
FLET_FLUTTER_BUNDLE="$ROOT_DIR/build/flutter/build/linux/x64/release/bundle"
BUILD_LOG="$ROOT_DIR/build/flet-build.log"
FLET_BIN=""
PYTHON_BIN=""
PIP_BIN=""
WORK_DIR=""
ICON_BACKUP=""

C_RESET=""
C_BOLD=""
C_DIM=""
C_CYAN=""
C_BLUE=""
C_GREEN=""
C_YELLOW=""
C_RED=""

usage() {
  cat <<USAGE
Usage: ./scripts/build_linux_packages.sh [version] [arch] [--verbose|-v]

Arguments:
  version   Package version (default: 2.0.0)
  arch      Target architecture: amd64 | arm64 (default: amd64)
  -v, --verbose   Stream full command output instead of compact mode
USAGE
}

parse_args() {
  local positional=()
  local arg
  for arg in "$@"; do
    case "$arg" in
      -v|--verbose)
        VERBOSE=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        positional+=("$arg")
        ;;
    esac
  done

  if [[ "${#positional[@]}" -gt 2 ]]; then
    log_error "Too many positional arguments."
    usage
    exit 1
  fi

  if [[ "${#positional[@]}" -ge 1 ]]; then
    VERSION="${positional[0]}"
  fi

  if [[ "${#positional[@]}" -ge 2 ]]; then
    ARCH="${positional[1]}"
  fi
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

setup_colors() {
  if [[ -t 1 ]] && have_command tput && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
    C_RESET="$(tput sgr0)"
    C_BOLD="$(tput bold)"
    C_DIM="$(tput dim)"
    C_CYAN="$(tput setaf 6)"
    C_BLUE="$(tput setaf 4)"
    C_GREEN="$(tput setaf 2)"
    C_YELLOW="$(tput setaf 3)"
    C_RED="$(tput setaf 1)"
  fi
}

log_header() {
  printf "%b\n" "${C_BOLD}${C_CYAN}==> $*${C_RESET}"
}

log_step() {
  printf "%b\n" "${C_BLUE}[..]${C_RESET} $*"
}

log_ok() {
  printf "%b\n" "${C_GREEN}[OK]${C_RESET} $*"
}

log_warn() {
  printf "%b\n" "${C_YELLOW}[!!]${C_RESET} $*"
}

log_error() {
  printf "%b\n" "${C_RED}[ER]${C_RESET} $*" >&2
}

show_banner() {
  printf "%b\n" "${C_BOLD}${C_CYAN}============================================================${C_RESET}"
  printf "%b\n" "${C_BOLD}${C_CYAN}  StreamNest Linux Package Builder${C_RESET}"
  printf "%b\n" "${C_DIM}  version=${VERSION}  arch=${ARCH}  verbose=${VERBOSE}${C_RESET}"
  printf "%b\n" "${C_BOLD}${C_CYAN}============================================================${C_RESET}"
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_error "Required command '$cmd' is not installed or not in PATH."
    exit 1
  fi
}

cleanup() {
  if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
    rm -rf "$WORK_DIR"
  fi

  if [[ -n "$ICON_BACKUP" && -f "$ICON_BACKUP" ]]; then
    mv -f "$ICON_BACKUP" "${ICON_BASE}.png"
  fi
}

run_with_optional_sudo() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif have_command sudo; then
    sudo "$@"
  else
    log_error "Need root privileges to install system dependencies, but 'sudo' is not available."
    return 1
  fi
}

install_appimagetool() {
  local arch="$1"
  local appimagetool_url=""
  local appimagetool_file=""

  case "$arch" in
    amd64|x86_64)
      appimagetool_url="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
      appimagetool_file="appimagetool-x86_64.AppImage"
      ;;
    arm64|aarch64)
      appimagetool_url="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-aarch64.AppImage"
      appimagetool_file="appimagetool-aarch64.AppImage"
      ;;
    *)
      log_error "Unsupported architecture for appimagetool: $arch"
      return 1
      ;;
  esac

  log_step "Downloading appimagetool from AppImageKit releases"
  if ! curl -L -o "$appimagetool_file" "$appimagetool_url"; then
    log_error "Failed to download appimagetool"
    return 1
  fi

  chmod +x "$appimagetool_file"
  sudo mv "$appimagetool_file" /usr/local/bin/appimagetool
  log_ok "appimagetool installed successfully"
}

install_apt_packages() {
  local packages=("$@")
  if [[ "${#packages[@]}" -eq 0 ]]; then
    log_ok "System dependencies already satisfied."
    return 0
  fi

  if ! have_command apt-get; then
    log_error "Missing required system packages and apt-get is unavailable."
    log_error "Install manually: ${packages[*]}"
    exit 1
  fi

  # Handle appimagetool specially - download from AppImageKit if not available via apt
  local apt_packages=()
  local appimagetool_needed=false

  for pkg in "${packages[@]}"; do
    if [[ "$pkg" == "appimagetool" ]]; then
      appimagetool_needed=true
    else
      apt_packages+=("$pkg")
    fi
  done

  if [[ "${#apt_packages[@]}" -gt 0 ]]; then
    log_header "Installing system dependencies"
    log_step "Installing via apt: ${apt_packages[*]}"
    if [[ "$VERBOSE" -eq 1 ]]; then
      run_with_optional_sudo apt-get update
      run_with_optional_sudo apt-get install -y "${apt_packages[@]}"
    else
      run_with_optional_sudo apt-get update -qq
      run_with_optional_sudo apt-get install -y -qq "${apt_packages[@]}"
    fi
  fi

  if [[ "$appimagetool_needed" == true ]]; then
    log_step "Installing appimagetool from AppImageKit releases"
    if ! install_appimagetool "$ARCH"; then
      log_error "Failed to install appimagetool"
      exit 1
    fi
  fi

  log_ok "System dependencies installed."
}

ensure_python_tools() {
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif have_command python3; then
    PYTHON_BIN="python3"
  elif have_command python; then
    PYTHON_BIN="python"
  else
    log_error "Python is required but not found (python3/python)."
    exit 1
  fi

  if [[ -x "$ROOT_DIR/.venv/bin/pip" ]]; then
    PIP_BIN="$ROOT_DIR/.venv/bin/pip"
  elif "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    PIP_BIN="$PYTHON_BIN -m pip"
  else
    log_error "pip is required but not available for '$PYTHON_BIN'."
    exit 1
  fi
}

ensure_python_requirements() {
  ensure_python_tools

  if [[ ! -f "$ROOT_DIR/pyproject.toml" ]]; then
    log_warn "pyproject.toml not found; skipping Python dependency installation."
    return 0
  fi

  log_header "Installing Python dependencies"
  if [[ "$VERBOSE" -eq 1 ]]; then
    # shellcheck disable=SC2086
    $PIP_BIN install --disable-pip-version-check -e "$ROOT_DIR"
  else
    # shellcheck disable=SC2086
    $PIP_BIN install --quiet --disable-pip-version-check -e "$ROOT_DIR"
  fi
  log_ok "Python dependencies are ready."
}

ensure_system_requirements() {
  local missing_packages=()
  local fuse_package=""

  have_command clang || missing_packages+=("clang")
  have_command cmake || missing_packages+=("cmake")
  have_command ninja || have_command ninja-build || missing_packages+=("ninja-build")
  have_command pkg-config || missing_packages+=("pkg-config")
  have_command desktop-file-validate || missing_packages+=("desktop-file-utils")
  have_command dpkg-deb || missing_packages+=("dpkg-dev")
  have_command appimagetool || missing_packages+=("appimagetool")
  have_command convert || missing_packages+=("imagemagick")

  if ! have_command ld.lld && ! have_command ld; then
    missing_packages+=("lld-20")
  fi

  # AppImage runtime requires libfuse.so.2 on the target machine.
  if ! ldconfig -p 2>/dev/null | grep -q 'libfuse\.so\.2'; then
    if apt-cache show libfuse2t64 >/dev/null 2>&1; then
      fuse_package="libfuse2t64"
    elif apt-cache show libfuse2 >/dev/null 2>&1; then
      fuse_package="libfuse2"
    fi

    if [[ -n "$fuse_package" ]]; then
      missing_packages+=("$fuse_package")
    else
      log_warn "libfuse.so.2 is missing and no apt package candidate was detected (tried: libfuse2t64, libfuse2)."
      log_warn "Built AppImages may fail to launch on this machine until a FUSE2 compatibility library is installed."
    fi
  fi

  # Deduplicate while preserving order.
  local deduped=()
  local seen=""
  local pkg
  for pkg in "${missing_packages[@]}"; do
    if [[ " $seen " != *" $pkg "* ]]; then
      deduped+=("$pkg")
      seen+=" $pkg"
    fi
  done

  install_apt_packages "${deduped[@]}"
}

prepare_launcher_icon() {
  local icon_file="${ICON_BASE}.png"
  if [[ ! -f "$icon_file" ]]; then
    return 0
  fi

  if ! have_command convert; then
    log_warn "ImageMagick 'convert' not found; skipping icon normalization."
    return 0
  fi

  local icon_type
  icon_type="$(identify -format '%[type]' "$icon_file" 2>/dev/null || true)"

  # flutter_launcher_icons can fail on some palette PNGs; force truecolor RGBA.
  if [[ "$icon_type" == Palette* ]]; then
    ICON_BACKUP="$(mktemp)"
    cp "$icon_file" "$ICON_BACKUP"
    convert "$icon_file" -alpha on -colorspace sRGB PNG32:"$icon_file"
    log_ok "Normalized launcher icon to PNG32 for stable icon generation."
  else
    log_step "Launcher icon format already compatible (${icon_type:-unknown})."
  fi
}

ensure_linux_linker() {
  local llvm_bin="/usr/lib/llvm-20/bin"
  if [[ -d "$llvm_bin" ]]; then
    export PATH="$llvm_bin:$PATH"
    if [[ ! -x "$llvm_bin/ld.lld" && ! -x "$llvm_bin/ld" ]]; then
      log_error "Flutter Linux build requires ld.lld or ld in $llvm_bin."
      log_error "Install linker tools first (Ubuntu example): sudo apt install lld-20"
      exit 1
    fi
  fi

  if ! command -v ld.lld >/dev/null 2>&1 && ! command -v ld >/dev/null 2>&1; then
    log_error "No usable linker found (ld.lld or ld)."
    exit 1
  fi

  log_ok "Linker check passed."
}

run_flet_linux_build() {
  mkdir -p "$(dirname "$BUILD_LOG")"
  : > "$BUILD_LOG"

  log_header "Running Flet build"
  log_step "Command: $FLET_BIN build --yes linux $ROOT_DIR"
  log_step "Build log: $BUILD_LOG"
  if [[ "$VERBOSE" -eq 1 ]]; then
    if "$FLET_BIN" build --yes --no-rich-output linux "$ROOT_DIR" 2>&1 | tee "$BUILD_LOG"; then
      log_ok "Flet Linux build completed."
      return
    fi

    log_warn "Initial build failed. Retrying once with --clear-cache..."
    {
      echo "----- retry with --clear-cache -----"
      "$FLET_BIN" build --yes --no-rich-output --clear-cache linux "$ROOT_DIR"
    } 2>&1 | tee -a "$BUILD_LOG" || exit 1
    log_ok "Flet Linux build completed on retry."
  else
    if "$FLET_BIN" build --yes --no-rich-output linux "$ROOT_DIR" >"$BUILD_LOG" 2>&1; then
      log_ok "Flet Linux build completed."
      return
    fi

    log_warn "Initial build failed. Retrying once with --clear-cache..."
    {
      echo "----- retry with --clear-cache -----"
      "$FLET_BIN" build --yes --no-rich-output --clear-cache linux "$ROOT_DIR"
    } >>"$BUILD_LOG" 2>&1 || {
      log_error "Flet build failed. Last 60 log lines:"
      tail -n 60 "$BUILD_LOG" | sed 's/^/  | /' >&2
      exit 1
    }

    log_ok "Flet Linux build completed on retry."
  fi
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

parse_args "$@"
case "$ARCH" in
  amd64|arm64) ;;
  *)
    log_error "Unsupported architecture '$ARCH'. Use amd64 or arm64."
    usage
    exit 1
    ;;
esac

setup_colors
trap cleanup EXIT
show_banner

ensure_system_requirements
ensure_python_requirements
require_command dpkg-deb
require_command desktop-file-validate
require_command appimagetool

if command -v flet >/dev/null 2>&1; then
  FLET_BIN="flet"
elif [[ -x "$ROOT_DIR/.venv/bin/flet" ]]; then
  FLET_BIN="$ROOT_DIR/.venv/bin/flet"
else
  log_error "'flet' not found in PATH and '$ROOT_DIR/.venv/bin/flet' does not exist."
  exit 1
fi

log_ok "Using Flet binary: $FLET_BIN"
ensure_linux_linker
prepare_launcher_icon
run_flet_linux_build

if ! BUILD_DIR="$(resolve_bundle_dir)"; then
  log_error "Built Linux bundle not found after 'flet build --yes linux'."
  log_error "Looked for executable '$EXECUTABLE' under '$ROOT_DIR/build'."
  exit 1
fi

log_ok "Using Linux bundle: $BUILD_DIR"

if [[ ! -f "${ICON_BASE}.png" ]]; then
  log_error "${ICON_BASE}.png was not found."
  exit 1
fi

mkdir -p "$OUT_DIR"
WORK_DIR="$(mktemp -d)"

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
log_header "Building .deb package"
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
log_ok "Created .deb package: $DEB_OUT"

# -----------------------------
# Build .AppImage
# -----------------------------
log_header "Building .AppImage package"
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
log_ok "Created .AppImage package: $APPIMAGE_OUT"

(
  cd "$OUT_DIR"
  sha256sum "$(basename "$DEB_OUT")" "$(basename "$APPIMAGE_OUT")" > "checksums-${VERSION}.sha256"
)

log_header "Build complete"
printf "%b\n" "${C_GREEN}  - $DEB_OUT${C_RESET}"
printf "%b\n" "${C_GREEN}  - $APPIMAGE_OUT${C_RESET}"
printf "%b\n" "${C_GREEN}  - $OUT_DIR/checksums-${VERSION}.sha256${C_RESET}"
