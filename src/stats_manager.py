from typing import List, Dict
import json
from datetime import datetime
import os

class StatsManager:
    def __init__(self):
        self.stats = {
            'total_pnl': 0.0,
            'opportunities_found': 0,
            'opportunities_taken': 0,
            'total_volume': 0.0,
            'trades': [],
            'preferred_tokens': set()
        }
        self.load_stats()
        
    def load_stats(self):
        """Charge les statistiques depuis le fichier"""
        try:
            if os.path.exists('stats.json'):
                with open('stats.json', 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
                    self.stats['preferred_tokens'] = set(saved_stats.get('preferred_tokens', []))
        except Exception as e:
            print(f"Erreur lors du chargement des stats: {e}")

    def save_stats(self):
        """Sauvegarde les statistiques dans un fichier"""
        try:
            with open('stats.json', 'w') as f:
                save_data = self.stats.copy()
                save_data['preferred_tokens'] = list(save_data['preferred_tokens'])
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des stats: {e}")

    def add_opportunity_found(self):
        """Incrémente le compteur d'opportunités trouvées"""
        self.stats['opportunities_found'] += 1
        self.save_stats()

    def add_trade(self, trade_data: Dict):
        """Ajoute un trade réalisé aux statistiques"""
        self.stats['opportunities_taken'] += 1
        self.stats['total_pnl'] += trade_data['profit_usdt']
        self.stats['total_volume'] += trade_data['volume_usdt']
        
        trade_info = {
            'timestamp': datetime.now().isoformat(),
            'pair': trade_data['pair'],
            'profit_usdt': trade_data['profit_usdt'],
            'volume_usdt': trade_data['volume_usdt'],
            'profit_percent': trade_data['profit_percent']
        }
        self.stats['trades'].append(trade_info)
        self.save_stats()

    def get_average_profit(self) -> float:
        """Calcule le profit moyen par opportunité"""
        if not self.stats['opportunities_taken']:
            return 0.0
        return self.stats['total_pnl'] / self.stats['opportunities_taken']

    def add_preferred_token(self, token_address: str):
        """Ajoute un token à la liste des préférés"""
        self.stats['preferred_tokens'].add(token_address.lower())
        self.save_stats()

    def remove_preferred_token(self, token_address: str):
        """Retire un token de la liste des préférés"""
        self.stats['preferred_tokens'].discard(token_address.lower())
        self.save_stats()

    def get_preferred_tokens(self) -> List[str]:
        """Retourne la liste des tokens préférés"""
        return list(self.stats['preferred_tokens'])

    def is_preferred_token(self, token_address: str) -> bool:
        """Vérifie si un token est dans la liste des préférés"""
        return token_address.lower() in self.stats['preferred_tokens']