import sys
import asyncio
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
    QCheckBox, QGroupBox, QHBoxLayout, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from src.web3_client import Web3Client
from src.dex_scanner import DexScanner
from src.arbitrage_logic import ArbitrageLogic
from src.stats_manager import StatsManager

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
        
        # État du bot
        self.is_running = False
        self.last_eth_price = 0
        
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
        control_group = QGroupBox("Paramètres")
        control_layout = QHBoxLayout()
        
        # Profit minimum
        self.min_profit_input = QLineEdit()
        self.min_profit_input.setPlaceholderText('Profit minimum (%)')
        control_layout.addWidget(QLabel("Profit min:"))
        control_layout.addWidget(self.min_profit_input)
        
        # Volume minimum
        volume_label = QLabel("Volume min: 25K USDT")
        control_layout.addWidget(volume_label)
        
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
        self.opportunities_table.setColumnCount(8)
        self.opportunities_table.setHorizontalHeaderLabels([
            'Paire', 'Prix Uniswap', 'Prix Sushiswap', 
            'Différence (%)', 'Volume (USDT)', 'Gas (USDT)',
            'Profit Net (USDT)', 'Action'
        ])
        self.opportunities_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.opportunities_table)
        
    def setup_stats_panel(self, layout):
        # En-tête des statistiques
        stats_header = QHBoxLayout()
        
        # PnL Total
        self.pnl_label = QLabel('PnL Total: 0.00 USDT')
        self.pnl_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        stats_header.addWidget(self.pnl_label)
        
        # Nombre d'opportunités
        self.opportunities_stats = QLabel('Opportunités: 0 trouvées / 0 prises')
        stats_header.addWidget(self.opportunities_stats)
        
        # Profit moyen
        self.avg_profit_label = QLabel('Profit moyen: 0.00%')
        stats_header.addWidget(self.avg_profit_label)
        
        layout.addLayout(stats_header)
        
        # Tableau des trades
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            'Date/Heure', 'Paire', 'Volume (USDT)', 
            'Gas (USDT)', 'Profit Net (USDT)', 'Profit (%)'
        ])
        layout.addWidget(self.trades_table)

    def setup_tokens_panel(self, layout):
        # Ajout de token
        add_token_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText('Adresse du token')
        add_token_layout.addWidget(self.token_input)
        
        add_button = QPushButton('Ajouter Token')
        add_button.clicked.connect(self.add_preferred_token)
        add_token_layout.addWidget(add_button)
        layout.addLayout(add_token_layout)
        
        # Liste des tokens
        self.preferred_tokens_table = QTableWidget()
        self.preferred_tokens_table.setColumnCount(3)
        self.preferred_tokens_table.setHorizontalHeaderLabels([
            'Adresse', 'Symbole', 'Action'
        ])
        layout.addWidget(self.preferred_tokens_table)
        self.update_preferred_tokens_table()
        
    async def scan_opportunities(self):
        """Scan et analyse les opportunités d'arbitrage"""
        if not self.is_running:
            return
            
        try:
            # Mise à jour du prix ETH
            self.last_eth_price = await self.web3_client.get_eth_price()
            
            # Scan des paires
            pairs = await self.scanner.scan_pairs()
            opportunities = []
            
            for pair in pairs:
                opportunity = self.arbitrage_logic.analyze_pair(pair, self.last_eth_price)
                if opportunity:
                    opportunities.append(opportunity)
                    self.stats_manager.add_opportunity_found()
            
            # Mise à jour du tableau des opportunités
            self.update_opportunities_table(opportunities)
            
        except Exception as e:
            self.show_error(f"Erreur lors du scan: {str(e)}")
            
    def update_opportunities_table(self, opportunities):
        """Met à jour le tableau des opportunités"""
        self.opportunities_table.setRowCount(len(opportunities))
        
        for i, opp in enumerate(opportunities):
            # Pair name
            self.opportunities_table.setItem(i, 0, QTableWidgetItem(opp['pair_data']['symbol']))
            
            # Prices
            self.opportunities_table.setItem(i, 1, QTableWidgetItem(f"{opp['uni_price']:.8f}"))
            self.opportunities_table.setItem(i, 2, QTableWidgetItem(f"{opp['sushi_price']:.8f}"))
            
            # Profit percentage
            profit_item = QTableWidgetItem(f"{opp['profit_percent']:.2f}%")
            profit_item.setForeground(QColor('green'))
            self.opportunities_table.setItem(i, 3, profit_item)
            
            # Volume
            self.opportunities_table.setItem(i, 4, QTableWidgetItem(f"{opp['volume_usdt']:.2f}"))
            
            # Gas cost
            self.opportunities_table.setItem(i, 5, QTableWidgetItem(f"{opp['gas_cost_usdt']:.2f}"))
            
            # Net profit
            net_profit_item = QTableWidgetItem(f"{opp['net_profit_usdt']:.2f}")
            net_profit_item.setForeground(QColor('green'))
            self.opportunities_table.setItem(i, 6, net_profit_item)
            
            # Action button
            if self.auto_mode.isChecked():
                status_text = "Auto" if opp['is_executing'] else "En attente"
            else:
                trade_button = QPushButton("Trader")
                trade_button.clicked.connect(lambda _, o=opp: self.execute_trade(o))
                self.opportunities_table.setCellWidget(i, 7, trade_button)
                
    def toggle_bot(self):
        """Démarre ou arrête le bot"""
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()
            
    def start_bot(self):
        """Démarre le bot"""
        if not self.web3_client.check_connection():
            self.show_error("Impossible de se connecter à Ethereum")
            return
            
        self.is_running = True
        self.start_button.setText('Arrêter')
        self.status_label.setText('Status: En cours de scan')
        self.scan_timer.start(5000)  # Scan toutes les 5 secondes
        self.stats_timer.start(1000)  # Mise à jour des stats toutes les secondes
        
    def stop_bot(self):
        """Arrête le bot"""
        self.is_running = False
        self.scan_timer.stop()
        self.stats_timer.stop()
        self.start_button.setText('Démarrer')
        self.status_label.setText('Status: Arrêté')
        
    def show_error(self, message):
        """Affiche une erreur"""
        QMessageBox.critical(self, "Erreur", message)
        
    def execute_trade(self, opportunity):
        """Exécute un trade d'arbitrage"""
        if self.auto_mode.isChecked():
            self.execute_trade_automatically(opportunity)
        else:
            self.show_trade_confirmation(opportunity)
            
    def execute_trade_automatically(self, opportunity):
        """Exécute automatiquement le trade"""
        asyncio.create_task(self._execute_trade(opportunity))
            
    async def _execute_trade(self, opportunity):
        """Exécute le trade et met à jour les statistiques"""
        try:
            # TODO: Implémenter l'exécution du trade
            pass
        except Exception as e:
            self.show_error(f"Erreur lors de l'exécution du trade: {str(e)}")
            
    def show_trade_confirmation(self, opportunity):
        """Affiche une boîte de dialogue de confirmation pour le trade manuel"""
        confirm = QMessageBox.question(
            self,
            "Confirmer le trade",
            f"Voulez-vous exécuter ce trade?\n\n"
            f"Paire: {opportunity['pair_data']['symbol']}\n"
            f"Profit attendu: {opportunity['profit_percent']:.2f}%\n"
            f"Volume: {opportunity['volume_usdt']:.2f} USDT\n"
            f"Gas estimé: {opportunity['gas_cost_usdt']:.2f} USDT\n"
            f"Profit net: {opportunity['net_profit_usdt']:.2f} USDT",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.execute_trade_automatically(opportunity)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArbitrageBot()
    window.show()
    sys.exit(app.exec())