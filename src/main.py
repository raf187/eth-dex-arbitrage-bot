import sys
import asyncio
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
    QCheckBox, QGroupBox, QHBoxLayout, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from web3_client import Web3Client
from dex_scanner import DexScanner
from arbitrage_logic import ArbitrageLogic
from stats_manager import StatsManager

# Le reste du code reste identique...