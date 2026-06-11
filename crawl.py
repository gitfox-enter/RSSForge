#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Slim entry point — all logic moved to crawler/ package."""

import sys

# Import the main function from the crawler package
from crawler.engine import main

if __name__ == '__main__':
    main()
