import argparse
import os
import logging


def main():
    """TODO: Implement following the current document"""
    logging.basicConfig(format="%(created)10.6f:%(levelname)s:%(message)s")
    logging.getLogger().setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
    description = "KPET - Kernel Patch-Evaluated Testing"
    parser = argparse.ArgumentParser(description=description)
    args = parser.parse_args()
    parser.print_help()
