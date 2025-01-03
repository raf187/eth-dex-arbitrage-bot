import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
    QCheckBox, QGroupBox, QHBoxLayout, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from web3_client import Web3Client
from dex_scanner import DexScanner
from arbitrage_logic import ArbitrageLogic
from stats_manager import StatsManager

class ArbitrageBot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bot Arbitrage DEX')
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialisation des composants
        self.web3_client = Web3Client()
        self.scanner = None
        self.arbitrage_logic = ArbitrageLogic(min_volume_usdt=25000)
        self.stats_manager = StatsManager()
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Timer pour le scan et les stats
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_opportunities)
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats_display)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Création des onglets
        tabs = QTabWidget()
        
        # Onglet principal
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)
        self.setup_control_panel(main_tab_layout)
        self.setup_opportunities_table(main_tab_layout)
        tabs.addTab(main_tab, "Trading")
        
        # Onglet statistiques
        stats_tab = QWidget()
        stats_tab_layout = QVBoxLayout(stats_tab)
        self.setup_stats_panel(stats_tab_layout)
        tabs.addTab(stats_tab, "Statistiques")
        
        # Onglet tokens préférés
        tokens_tab = QWidget()
        tokens_tab_layout = QVBoxLayout(tokens_tab)
        self.setup_tokens_panel(tokens_tab_layout)
        tabs.addTab(tokens_tab, "Tokens Préférés")
        
        main_layout.addWidget(tabs)
        
    def setup_control_panel(self, layout):
        control_group = QGroupBox("Contrôles")
        control_layout = QHBoxLayout()
        
        # Paramètres de trading
        self.min_profit_input = QLineEdit()
        self.min_profit_input.setPlaceholderText('Profit minimum (%)')
        control_layout.addWidget(QLabel("Profit min:"))
        control_layout.addWidget(self.min_profit_input)
        
        # Mode automatique/manuel
        self.auto_mode = QCheckBox("Mode Automatique")
        control_layout.addWidget(self.auto_mode)
        
        # Bouton démarrer/arrêter
        self.start_button = QPushButton('Démarrer')
        self.start_button.clicked.connect(self.toggle_bot)
        control_layout.addWidget(self.start_button)
        
        # Status
        self.status_label = QLabel('Status: Déconnecté')
        control_layout.addWidget(self.status_label)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
    def setup_opportunities_table(self, layout):
        self.opportunities_table = QTableWidget()
        self.opportunities_table.setColumnCount(7)
        self.opportunities_table.setHorizontalHeaderLabels([
            'Paire', 'Prix Uniswap', 'Prix Sushiswap', 
            'Différence (%)', 'Volume (USDT)', 'Direction', 'Action'
        ])
        layout.addWidget(self.opportunities_table)
        
    def setup_stats_panel(self, layout):
        stats_grid = QVBoxLayout()
        
        # Statistiques principales
        self.pnl_label = QLabel('PnL Total: 0.00 USDT')
        self.pnl_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        stats_grid.addWidget(self.pnl_label)
        
        self.opportunities_found_label = QLabel('Opportunités trouvées: 0')
        stats_grid.addWidget(self.opportunities_found_label)
        
        self.opportunities_taken_label = QLabel('Trades réalisés: 0')
        stats_grid.addWidget(self.opportunities_taken_label)
        
        self.avg_profit_label = QLabel('Profit moyen: 0.00%')
        stats_grid.addWidget(self.avg_profit_label)
        
        # Tableau des derniers trades
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(5)
        self.trades_table.setHorizontalHeaderLabels([
            'Date/Heure', 'Paire', 'Profit USDT', 'Volume USDT', 'Profit %'
        ])
        stats_grid.addWidget(self.trades_table)
        
        layout.addLayout(stats_grid)
        
    def setup_tokens_panel(self, layout):
        tokens_layout = QVBoxLayout()
        
        # Ajouter un nouveau token
        add_token_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText('Adresse du token')
        add_token_layout.addWidget(self.token_input)
        
        add_button = QPushButton('Ajouter Token')
        add_button.clicked.connect(self.add_preferred_token)
        add_token_layout.addWidget(add_button)
        tokens_layout.addLayout(add_token_layout)
        
        # Liste des tokens préférés
        self.preferred_tokens_table = QTableWidget()
        self.preferred_tokens_table.setColumnCount(3)
        self.preferred_tokens_table.setHorizontalHeaderLabels([
            'Adresse', 'Symbole', 'Action'
        ])
        tokens_layout.addWidget(self.preferred_tokens_table)
        
        layout.addLayout(tokens_layout)
        
    def update_stats_display(self):
        """Met à jour l'affichage des statistiques"""
        stats = self.stats_manager.stats
        
        self.pnl_label.setText(f'PnL Total: {stats["total_pnl"]:.2f} USDT')
        self.opportunities_found_label.setText(f'Opportunités trouvées: {stats["opportunities_found"]}')
        self.opportunities_taken_label.setText(f'Trades réalisés: {stats["opportunities_taken"]}')
        self.avg_profit_label.setText(f'Profit moyen: {self.stats_manager.get_average_profit():.2f}%')
        
        # Mise à jour du tableau des trades
        self.update_trades_table()
        
    def update_trades_table(self):
        """Met à jour le tableau des derniers trades"""
        trades = self.stats_manager.stats['trades']
        self.trades_table.setRowCount(len(trades))
        
        for i, trade in enumerate(reversed(trades)):
            self.trades_table.setItem(i, 0, QTableWidgetItem(trade['timestamp']))
            self.trades_table.setItem(i, 1, QTableWidgetItem(trade['pair']))
            self.trades_table.setItem(i, 2, QTableWidgetItem(f"{trade['profit_usdt']:.2f}"))
            self.trades_table.setItem(i, 3, QTableWidgetItem(f"{trade['volume_usdt']:.2f}"))
            self.trades_table.setItem(i, 4, QTableWidgetItem(f"{trade['profit_percent']:.2f}%"))
            
    def add_preferred_token(self):
        """Ajoute un token à la liste des préférés"""
        token_address = self.token_input.text().strip()
        if Web3.is_address(token_address):
            self.stats_manager.add_preferred_token(token_address)
            self.token_input.clear()
            self.update_preferred_tokens_table()
        else:
            QMessageBox.warning(self, "Erreur", "Adresse de token invalide")
            
    def update_preferred_tokens_table(self):
        """Met à jour la liste des tokens préférés"""
        tokens = self.stats_manager.get_preferred_tokens()
        self.preferred_tokens_table.setRowCount(len(tokens))
        
        for i, token in enumerate(tokens):
            self.preferred_tokens_table.setItem(i, 0, QTableWidgetItem(token))
            # TODO: Ajouter le symbole du token
            
            remove_button = QPushButton('Retirer')
            remove_button.clicked.connect(lambda _, t=token: self.remove_preferred_token(t))
            self.preferred_tokens_table.setCellWidget(i, 2, remove_button)
            
    def remove_preferred_token(self, token_address):
        """Retire un token de la liste des préférés"""
        self.stats_manager.remove_preferred_token(token_address)
        self.update_preferred_tokens_table()
        
    def toggle_bot(self):
        if self.scan_timer.isActive():
            self.scan_timer.stop()
            self.stats_timer.stop()
            self.start_button.setText('Démarrer')
            self.status_label.setText('Status: Arrêté')
        else:
            if self.web3_client.check_connection():
                self.scan_timer.start(5000)  # Scan toutes les 5 secondes
                self.stats_timer.start(1000)  # Mise à jour des stats toutes les secondes
                self.start_button.setText('Arrêter')
                self.status_label.setText('Status: En cours de scan')
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de se connecter à Ethereum")