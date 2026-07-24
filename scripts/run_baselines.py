import sys

from cbench.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["baseline", *sys.argv[1:]]))
