"""
public_interface package initializer.

This file makes `public_interface` a package so that imports like
`from public_interface.bunny_signer import ...` work whether the app
is executed via `python -m public_interface.public_interface` or when
tests import modules directly.

Keep this minimal to avoid module-level side effects during import.
"""

__all__ = [
    "public_interface",
]
