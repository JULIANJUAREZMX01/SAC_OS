import sys
import os

# Ensure the current directory is in the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sacity_shell import SacityShell
except ImportError:
    print("Error: Could not import sacity_shell. Make sure sacity_tui.py and sacity_shell.py are in the same directory.")
    sys.exit(1)

def main():
    # This is the main entry point for the SACITY Client on the device.
    # It initializes the Shell, which handles the UI and user interaction.
    shell = SacityShell()
    shell.run()

if __name__ == "__main__":
    main()
