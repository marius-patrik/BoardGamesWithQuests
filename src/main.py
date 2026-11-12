"""Launch the offline Chess desktop from source or a frozen Windows executable."""

from view.app import run


def main() -> None:
    """Run the same user-facing Tkinter interface in every distribution."""
    run()


if __name__ == "__main__":
    main()
