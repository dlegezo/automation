#!/usr/bin/env python3
"""Shared utility helpers for CTI parser scripts."""

from __future__ import annotations

from typing import Set


def normalize_tag(value: str) -> str:
    return value.strip().lower()


def jaccard_distance(left: Set[str], right: Set[str]) -> float:
    """Return Jaccard distance in [0.0, 1.0]."""
    union = left | right
    if not union:
        return 0.0
    similarity = len(left & right) / len(union)
    return 1.0 - similarity
