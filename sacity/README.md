# SACITY - Symbol MC9190 Deployment System

SACITY is a lightweight, open-source alternative to commercial Telnet/Velocity emulators, specifically designed for Symbol MC9190 devices running Windows CE 6.0. It features a stylized ASCII interface with a red/orange/blue color scheme and minimal resource usage.

## Components

1.  **SACITY Installer Suite (`sacity_installer_suite.py`)**: A PC-side Python tool to manage the deployment process.
    *   Detects devices via USB (ActiveSync/WMDC) or Network.
    *   Analyzes device state.
    *   Installs necessary drivers (placeholders).
    *   Optimizes the device (clears temp files).
    *   Deploys the SACITY Client.
    *   Configures the device.

2.  **SACITY Client (`sacity_client_ce.py`)**: The emulator application for the MC9190.
    *   **Note**: Requires a Python environment on the Windows CE device.
    *   Implements a basic Telnet client.
    *   Handles VT100/ANSI escape sequences.
    *   Provides a custom ASCII-based UI.
    *   Manages scanner input.

## Usage

### Installer (PC)

```bash
cd sacity
python sacity_installer_suite.py
```

Follow the on-screen menu to detect devices and deploy the client.

### Client (Device)

Once deployed, the client can be started from the device (assuming Python is installed and configured).

## Architecture

The system bridges the gap between modern PC management and legacy Windows CE devices, ensuring a smooth deployment pipeline for the custom SACITY emulator.
