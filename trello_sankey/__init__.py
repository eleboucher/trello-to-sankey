"""
Trello to SankeyMATIC Data Generator

A Python package for analyzing Trello job board card movements and generating
data in SankeyMATIC format for visualization of job application flow.
"""

from .config import TrelloConfig
from .generator import TrelloSankeyGenerator
from .models import CardHistory, FlowData, SankeyData

__version__ = "0.1.0"
__all__ = [
    "TrelloSankeyGenerator",
    "CardHistory",
    "FlowData",
    "SankeyData",
    "TrelloConfig",
]
