# SACITY Installer Suite - User Guide

This guide explains how to use the SACITY Installer Suite to deploy the SACITY emulator to Symbol MC9190 devices.

## Prerequisites

*   **PC**: Windows 10/11
*   **Software**: Python 3.x installed
*   **Connectivity**: 
    *   USB Cable + Docking Station (requires Windows Mobile Device Center)
    *   OR Network connection (WiFi/Ethernet) to the device

## Installation Steps

1.  **Connect the Device**:
    *   Place the MC9190 in the cradle.
    *   Ensure it is connected to the PC via USB or on the same network.

2.  **Run the Installer**:
    Open a command prompt in the `sacity` folder and run:
    ```bash
    python sacity_installer_suite.py
    ```

3.  **Select Mode**:
    *   **Option 1 (Full Installation)**: Checks drivers, optimizes storage, and deploys the client. Recommended for first-time setup.
    *   **Option 2 (Update Client)**: Only updates the `sacity_client_ce.py` file.
    *   **Option 3 (Update Config)**: Pushes a new `sacity_config.json`.

## Troubleshooting

*   **Device Not Found (USB)**: Ensure Windows Mobile Device Center is running and the device is paired.
*   **Connection Failed**: Check the IP address in `sacity_config_template.json` matches your WMS server.
*   **Python Error on Device**: The MC9190 must have a Python runtime installed. If not, the client will not run.

## Configuration

Edit `sacity_config_template.json` to change:
*   Target Host IP/Port
*   Color Schemes
*   Scanner Prefixes/Suffixes
