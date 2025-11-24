import sys
import time
import random
import os

class SacityColors:
    # ANSI Escape Codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Standard ANSI mapping (approximate to requested palette)
    # Red (#E31837) -> ANSI Red
    RED = "\033[31m"
    # Green (#00FF88) -> ANSI Green (or Bright Green)
    GREEN = "\033[92m" 
    # Cyan (#00C8FF) -> ANSI Cyan (or Bright Cyan)
    CYAN = "\033[96m"
    # Grey -> ANSI Bright Black
    GREY = "\033[90m"
    
    # Backgrounds
    BG_BLACK = "\033[40m"

class SacityScreen:
    @staticmethod
    def clear():
        # Clear screen and move cursor to top-left
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    @staticmethod
    def move_cursor(row, col):
        sys.stdout.write(f"\033[{row};{col}H")
        sys.stdout.flush()

    @staticmethod
    def print_at(row, col, text, color=SacityColors.RESET):
        SacityScreen.move_cursor(row, col)
        sys.stdout.write(f"{color}{text}{SacityColors.RESET}")
        sys.stdout.flush()

    @staticmethod
    def draw_box(row, col, width, height, color=SacityColors.RED):
        # Top border
        SacityScreen.print_at(row, col, "┌" + "─" * (width - 2) + "┐", color)
        # Side borders
        for r in range(row + 1, row + height - 1):
            SacityScreen.print_at(r, col, "│", color)
            SacityScreen.print_at(r, col + width - 1, "│", color)
        # Bottom border
        SacityScreen.print_at(row + height - 1, col, "└" + "─" * (width - 2) + "┘", color)

class SacityAnimations:
    @staticmethod
    def type_writer(text, color=SacityColors.GREEN, delay=0.03):
        sys.stdout.write(color)
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write(SacityColors.RESET + "\n")

    @staticmethod
    def loading_bar(label, duration=2, width=40, color=SacityColors.CYAN):
        steps = width
        sleep_time = duration / steps
        sys.stdout.write(f"{SacityColors.GREY}{label} [")
        for i in range(steps):
            sys.stdout.write(f"{color}=")
            sys.stdout.flush()
            time.sleep(sleep_time)
        sys.stdout.write(f"{SacityColors.GREY}] {SacityColors.GREEN}OK{SacityColors.RESET}\n")

    @staticmethod
    def matrix_rain(duration=3):
        # Simple matrix rain effect
        width = 80
        height = 24
        end_time = time.time() + duration
        chars = "01"
        
        while time.time() < end_time:
            col = random.randint(1, width)
            row = random.randint(1, height)
            char = random.choice(chars)
            SacityScreen.print_at(row, col, char, SacityColors.GREEN)
            time.sleep(0.01)
        SacityScreen.clear()

    @staticmethod
    def startup_sequence():
        SacityScreen.clear()
        SacityAnimations.matrix_rain(2)
        SacityScreen.clear()
        
        logo = [
            "  ____    _    ____ ___ _______   __",
            " / ___|  / \\  / ___|_ _|_   _\\ \\ / /",
            " \\___ \\ / _ \\| |    | |  | |  \\ V / ",
            "  ___) / ___ \\ |___ | |  | |   | |  ",
            " |____/_/   \\_\\____|___| |_|   |_|  "
        ]
        
        row = 5
        for line in logo:
            SacityScreen.print_at(row, 20, line, SacityColors.RED)
            row += 1
            time.sleep(0.1)
            
        SacityScreen.print_at(12, 28, "OPERATING SYSTEM v1.0", SacityColors.GREY)
        time.sleep(1)
        
        SacityScreen.move_cursor(15, 1)
        SacityAnimations.loading_bar("Initializing Kernel...", 1)
        SacityAnimations.loading_bar("Loading Network Stack...", 1)
        SacityAnimations.loading_bar("Mounting Filesystem...", 0.5)
        
        time.sleep(0.5)
        SacityScreen.clear()

if __name__ == "__main__":
    # Test the TUI
    SacityAnimations.startup_sequence()
    SacityScreen.draw_box(2, 2, 76, 20, SacityColors.RED)
    SacityScreen.print_at(4, 4, "SYSTEM READY", SacityColors.GREEN)
    SacityScreen.move_cursor(22, 1)
