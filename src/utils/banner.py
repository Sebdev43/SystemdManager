BLUE = "\033[34m"
CYAN = "\033[36m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"


def print_banner():
    # Clear the screen via ANSI escapes (the app already requires an ANSI
    # terminal — see the colour codes above) instead of shelling out.
    print("\033[2J\033[H", end="")
    print("")
    print(f"{BLUE}")
    print("  ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗██████╗     ")
    print("  ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║██╔══██╗    ")
    print("  ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║██║  ██║    ")
    print("  ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║██║  ██║    ")
    print("  ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║██████╔╝    ")
    print(f"  ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═════╝     {RESET}")
    print("")
    print(f"{CYAN}                 SYSTEMD MANAGER                  {RESET}")
    print(f"{ITALIC}{BOLD}          Service Management Made Easy           {RESET}")
    print("")
    print(f" {BOLD}   SystemD Manager {RED}{ITALIC}(Linux v1.2.0) ⚡   {RESET}")
    print("")
    print(f"{GREEN}{ITALIC}              Developed by SEBDEV43              {RESET}")
    print("")
