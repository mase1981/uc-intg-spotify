"""Entry point for python -m. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
import asyncio

from uc_intg_spotify import main

if __name__ == "__main__":
    asyncio.run(main())
