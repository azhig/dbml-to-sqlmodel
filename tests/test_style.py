#!/usr/bin/env python3
"""Test script to check questionary styling."""

import questionary
from questionary import Style

# Custom style for testing
test_style = Style(
    [
        ("qmark", "fg:#00d7ff bold"),
        ("question", "fg:#ffffff bold"),
        ("answer", "fg:#00ff87 bold"),
        ("pointer", "fg:#ffff00 bold"),
        ("highlighted", "fg:#000000 bold bg:#ffff00 underline"),
        ("selected", "fg:#00ff87"),
        ("text", ""),
    ]
)


def main():
    choice = questionary.select(
        "Test menu - move with arrows to see highlighting:",
        choices=[
            "Option 1",
            "Option 2 (with underline on yellow bg)",
            "Option 3",
            "Exit",
        ],
        style=test_style,
    ).ask()

    print(f"\nYou selected: {choice}")


if __name__ == "__main__":
    main()
