# SACITY Shell - User Guide

The SACITY Shell is a minimalist command-line interface designed for speed and efficiency on the MC9190.

## Interface
*   **Style**: "Hacker-chic" / Unix-like
*   **Colors**:
    *   <span style="color:red">**RED**</span>: System prompts, Errors, Borders
    *   <span style="color:green">**GREEN**</span>: Success messages, Active status
    *   <span style="color:cyan">**CYAN**</span>: Information, Loading bars

## Commands

### `connect <host> [port]`
Connects to a Telnet server (WMS).
*   **Usage**: `connect 192.168.1.50` or `connect 192.168.1.50 2323`
*   **Default Port**: 23

### `scan`
Scans for available WiFi networks and nearby devices.
*   **Output**: List of SSIDs and signal strength.

### `status`
Displays current system health.
*   **Info**: Battery level, Memory usage, IP address, Connection state.

### `clear`
Clears the terminal screen.

### `exit`
Disconnects from current session or shuts down the shell (returns to OS if applicable).

## Shortcuts
*   **Ctrl+C**: Interrupt current command or disconnect from Telnet session.
