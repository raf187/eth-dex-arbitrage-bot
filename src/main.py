import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
    QCheckBox, QGroupBox, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from web3_client import Web3Client
from dex_scanner import DexScanner
from arbitrage_logic import ArbitrageLogic

class ArbitrageBot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bot Arbitrage DEX')
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialisation des composants
        self.web3_client = Web3Client()
        self.scanner = None
        self.arbitrage_logic = ArbitrageLogic(min_volume_usdt=25000)
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Timer pour le scan
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_opportunities)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Groupe des paramètres
        params_group = QGroupBox("Paramètres")
        params_layout = QHBoxLayout()
        
        # Paramètres de trading
        self.min_profit_input = QLineEdit()
        self.min_profit_input.setPlaceholderText('Profit minimum (%)')
        params_layout.addWidget(QLabel("Profit min:"))
        params_layout.addWidget(self.min_profit_input)
        
        # Mode automatique/manuel
        self.auto_mode = QCheckBox("Mode Automatique")
        params_layout.addWidget(self.auto_mode)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # Tableau des opportunités
        self.opportunities_table = QTableWidget()
        self.opportunities_table.setColumnCount(7)
        self.opportunities_table.setHorizontalHeaderLabels([
            'Paire', 'Prix Uniswap', 'Prix Sushiswap', 
            'Différence (%)', 'Volume (USDT)', 'Direction', 'Action'
        ])
        main_layout.addWidget(self.opportunities_table)
        
        # Boutons de contrôle
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton('Démarrer')
        self.start_button.clicked.connect(self.toggle_bot)
        control_layout.addWidget(self.start_button)
        
        self.status_label = QLabel('Status: Déconnecté')
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        
    def toggle_bot(self):
        if self.scan_timer.isActive():
            self.scan_timer.stop()
            self.start_button.setText('Démarrer')
            self.status_label.setText('Status: Arrêté')
        else:
            if self.web3_client.check_connection():
                self.scan_timer.start(5000)  # Scan toutes les 5 secondes
                self.start_button.setText('Arrêter')
                self.status_label.setText('Status: En cours de scan')
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de se connecter à Ethereum")
    
    def scan_opportunities(self):
        """Scan et affiche les opportunités d'arbitrage"""
        # TODO: Implémenter le scan des opportunités
        # Cette méthode sera appelée toutes les 5 secondes
        pass
    
    def execute_trade(self, opportunity):
        """Exécute un trade d'arbitrage"""
        if self.auto_mode.isChecked():
            # Mode automatique
            self.execute_trade_automatically(opportunity)
        else:
            # Mode manuel
            self.show_trade_confirmation(opportunity)
    
    def execute_trade_automatically(self, opportunity):
        """Exécute automatiquement le trade"""
        # TODO: Implémenter l'exécution automatique
        pass
    
    def show_trade_confirmation(self, opportunity):
        """Affiche une boîte de dialogue de confirmation pour le trade manuel"""
        confirm = QMessageBox.question(
            self,
            "Confirmer le trade",
            f"Voulez-vous exécuter ce trade?\n\n"
            f"Paire: {opportunity['pair']}\n"
            f"Profit attendu: {opportunity['profit_percent']:.2f}%\n"
            f"Volume: {opportunity['volume_usdt']:.2f} USDT",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.execute_trade_automatically(opportunity)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArbitrageBot()
    window.show()
    sys.exit(app.exec())