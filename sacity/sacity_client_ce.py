import sys
import os

# Ensure the current directory is in the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sacity.sacity_shell import SacityShell

def main():
    # This is the main entry point for the SACITY Client on the device.
    # It initializes the Shell, which handles the UI and user interaction.
    shell = SacityShell()
    shell.run()

if __name__ == "__main__":
    main()
