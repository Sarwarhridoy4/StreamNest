
# Linux Build Instructions for StreamNest

This document provides detailed instructions to build the StreamNest Media Downloader as a Linux executable using Flet.

## Prerequisites

- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.11.x (recommended)
- **Flet CLI**: Installed via uv
- **Flutter SDK**: Automatically downloaded by Flet if missing
- **Build Tools**: Required Linux packages for Flutter desktop builds

> IMPORTANT:
> Python 3.14 requires a workaround for Linux builds due to macro redefinition errors.
> Use the `CXXFLAGS` flag as shown in the troubleshooting section below.

## Installing System Dependencies

On Ubuntu/Debian-based systems:

```bash
sudo apt update

sudo apt install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    openjdk-17-jdk \
    clang \
    cmake \
    ninja-build \
    pkg-config \
    libgtk-3-dev \
    software-properties-common
````

## Install Python 3.11

Python 3.11 is recommended for stable Flet builds. Installation varies by distribution.

## Ubuntu/Debian (including Ubuntu 26.04 LTS)

Ubuntu 26.04 may not include Python 3.11 in the default repository.

Add the Deadsnakes PPA:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
```

Install Python 3.11:

```bash
sudo apt install python3.11 python3.11-venv python3.11-dev
```

Verify installation:

```bash
python3.11 --version
```

Expected output:

```txt
Python 3.11.x
```

## Fedora

On Fedora 40+:

```bash
    sudo dnf install python3.11 python3.11-devel
```

Verify:

```bash
python3.11 --version
```

## Arch Linux

Python 3.11 is available in the official repositories:

```bash
sudo pacman -S python311
```

## Other Distributions

For other Linux distributions, check your package manager for python3.11 or python311 packages. If not available, consider using pyenv for installation:

```bash
# Install pyenv dependencies (example for Ubuntu/Debian)
sudo apt install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add to shell profile
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9

# Verify
python --version
```

## Project Structure

The project follows the required Flet structure:

* `pyproject.toml` → Project configuration
* `main.py` → Application entry point
* `requirements.txt` → Python dependencies
* `assets/` → Icons, splash screens, etc.

## Create Virtual Environment

Remove old environments first:

```bash
rm -rf .venv
```

Create a new Python 3.11 environment:

```bash
python3.11 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Verify Python version:

```bash
python --version
```

Expected:

```txt
Python 3.11.x
```

## Install Dependencies

Upgrade uv:

```bash
uv pip install -U pip
```

Install project dependencies:

```bash
uv pip install -e .
```

Install/update Flet tools:

```bash
uv pip install -U flet flet-cli
```

## Verify Environment

Run:

```bash
flet doctor
```

Expected output example:

```txt
Flet 0.85.0 on Linux
Python 3.11.x
```

## Clean Previous Build Artifacts

Before building:

```bash
flutter clean
rm -rf build .dart_tool
```

## Build the Linux Executable

Run:

```bash
flet build linux
```

This command will:

* Download Flutter SDK if missing
* Create Flutter desktop shell
* Package Python dependencies
* Build the Linux executable

## Build Output

Generated files will be located in:

```txt
build/linux/
```

The executable can be distributed directly to compatible Linux systems.

## Run the Built Application

Example:

```bash
./build/linux/streamnest
```

## Configuration

Build configuration is defined in `pyproject.toml`.

Example values:

* Organization: `com.sarwarhridoy4`
* Product Name: `StreamNest`
* Company: `Sarwar Hossain`
* Entry Module: `main.py`

Additional Linux-specific settings can be added under:

```toml
[tool.flet.linux]
```

## Troubleshooting

## Flet 0.85.0 Macro Redefinition Error

If you see errors like:

```txt
_POSIX_C_SOURCE macro redefined [-Werror,-Wmacro-redefined]
_XOPEN_SOURCE macro redefined [-Werror,-Wmacro-redefined]
```

This is a known issue in Flet 0.85.0 where the embedded Python 3.12 build fails due to strict compiler warnings.

Fix:

```bash
export CXXFLAGS="-Wno-macro-redefined" && flet build linux
```

## Python 3.14 Build Error

If you see errors like:

```txt
_POSIX_C_SOURCE macro redefined
_XOPEN_SOURCE macro redefined
```

You are likely using Python 3.14.

Fix:

Use the following command to build with Python 3.14:

```bash
export CXXFLAGS="-Wno-macro-redefined" && flet build linux
```

Alternatively, switch to Python 3.11 for stable builds without workarounds.

## Android SDK Warning

Example warning:

```txt
Unable to locate Android SDK
```

This does NOT affect Linux desktop builds.

Only required for Android APK builds.

Install Android Studio if Android support is needed:

[Android Studio](https://developer.android.com/studio?utm_source=chatgpt.com)

## Verbose Build Logs

For detailed debugging:

```bash
flet build linux -v
export CXXFLAGS="-Wno-macro-redefined" && flet build linux
```

## Additional Notes# Additional Notes

* First build may take several minutes
* Flutter SDK is downloaded automatically
* Final executable is self-contained
* Recommended Python version: 3.11.x
* Python 3.14 is supported with the `CXXFLAGS` workaround
