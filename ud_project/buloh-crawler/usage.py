from termcolor import cprint

# Describe how to use the script
cprint("-" * 30, "green", attrs=["bold"])
cprint("RADAR Crawler CLI!", "green", attrs=["bold"])
cprint("-" * 30, "green", attrs=["bold"])
cprint(
    "Usage: python run.py --type <username/keyword/trending> --username <username> --keyword <keyword>",
    "green",
    attrs=["bold"],
)
cprint(
    "Username Example: python run.py --type username --username buddyxgold",
    "yellow",
)
cprint(
    "Keyword Example: python run.py --type keyword --keyword forex",
    "yellow",
)
cprint(
    "Trending Example: python run.py --type trending",
    "yellow",
)
cprint("-" * 30, "green", attrs=["bold"])
