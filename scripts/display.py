"""
This script is to be run by workshop organizers. It should be run for each available challenge in different terminals, 
plus one time to display the overall leaderboard.

It periodically looks for a CSV file corresponding to a given challenge image in the Leaderboard/ folder 
and displays the CSV contents nicely in a terminal.

Examples:

Run the leaderboard for the 'sheep' challenge:

```bash
python display.py sheep
```

For the overall score:

```bash
python display.py leaderboard
```
"""

from pathlib import Path
import sys
import pandas as pd
import os
import time
from tabulate import tabulate
from colorama import Fore, Style, init

# Refresh rate of the script
UPDATE_INTERVAL_SEC = 5

def clear_screen():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

def display_csv_content(csv_file, challenge):
    """Displays the content of the CSV file in a formatted way."""
    try:
        df = pd.read_csv(csv_file)
        formatted_table = tabulate(df, headers="keys", tablefmt="fancy_grid", showindex=False)
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Challenge: {challenge}{Style.RESET_ALL}")
        print(formatted_table)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: File '{csv_file}' not found.{Style.RESET_ALL}")
    except pd.errors.EmptyDataError:
        print(f"{Fore.YELLOW}Warning: File '{csv_file}' is empty.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")

if __name__ == '__main__':
    init(autoreset=True)  # Initialize colorama for auto-resetting styles
    
    _, challenge = sys.argv  # Challenge name is the first argument of the script
    
    root = Path(__file__)
    
    csv_file = root.parents[1] / "Leaderboard" / f"{challenge}.csv"
    if not csv_file.exists():
        raise FileNotFoundError(csv_file)

    while True:
        clear_screen()
        display_csv_content(csv_file, challenge)
        time.sleep(UPDATE_INTERVAL_SEC)