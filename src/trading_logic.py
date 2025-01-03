from typing import Dict, List, Optional
from web3 import Web3
from decimal import Decimal
import time

class TradingLogic:
    def __init__(self, web3_client, trade_executor, stats_manager):
        self.w3 = web3_client
        self.executor = trade_executor
        self.stats = stats_manager
        self.MAX_SLIPPAGE = 0.01  # 1%
        self.TRANSACTION_TIMEOUT = 240  # 4 minutes
        self.USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
        
    async def analyze_opportunity(self, pair_data: Dict) -> Optional[Dict]:
        """Analyse une opportunité d'arbitrage"""
        try:
            # Vérification si les tokens sont dans la liste préférée
            if len(self.stats.get_preferred_tokens()) > 0:
                if not (self.stats.is_preferred_token(pair_data['token0']) or 
                        self.stats.is_preferred_token(pair_data['token1'])):
                    return None

            # Calcul du profit net estimé
            gas_price = await self.w3.eth.get_gas_price()
            estimated_gas = 300000  # Estimation pour un arbitrage complet
            gas_cost_eth = gas_price * estimated_gas
            gas_cost_usdt = await self.get_eth_price_in_usdt() * gas_cost_eth / 1e18

            # Ajout du coût du gas au calcul du profit net
            net_profit_usdt = pair_data['expected_profit_usdt'] - gas_cost_usdt
            
            if net_profit_usdt <= 0:
                return None

            return {
                **pair_data,
                'net_profit_usdt': net_profit_usdt,
                'gas_cost_usdt': gas_cost_usdt,
                'deadline': int(time.time()) + self.TRANSACTION_TIMEOUT,
                'max_slippage': self.MAX_SLIPPAGE
            }

        except Exception as e:
            print(f"Erreur lors de l'analyse de l'opportunité: {e}")
            return None

    async def execute_opportunity(self, opportunity: Dict) -> Dict:
        """Exécute une opportunité d'arbitrage"""
        try:
            # Vérification finale des prix avant exécution
            current_prices = await self.verify_prices(opportunity)
            if not self.is_opportunity_still_valid(opportunity, current_prices):
                return {'success': False, 'error': 'Prix changés, opportunité non valide'}

            # Exécution du trade
            trade_result = await self.executor.execute_arbitrage(opportunity)
            
            if trade_result['success']:
                # Mise à jour des statistiques
                self.update_stats(opportunity, trade_result)
                return {'success': True, 'trade_result': trade_result}
            else:
                return {'success': False, 'error': trade_result['error']}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def verify_prices(self, opportunity: Dict) -> Dict:
        """Vérifie les prix actuels avant l'exécution"""
        # Implémentation de la vérification des prix en temps réel
        uni_price = await self.get_current_price(opportunity['token_pair'], 'uniswap')
        sushi_price = await self.get_current_price(opportunity['token_pair'], 'sushiswap')
        
        return {
            'uniswap_price': uni_price,
            'sushiswap_price': sushi_price
        }

    def is_opportunity_still_valid(self, opportunity: Dict, current_prices: Dict) -> bool:
        """Vérifie si l'opportunité est toujours valide avec les prix actuels"""
        original_profit = opportunity['profit_percent']
        current_profit = abs(
            (current_prices['uniswap_price'] - current_prices['sushiswap_price']) /
            min(current_prices['uniswap_price'], current_prices['sushiswap_price'])
        ) * 100

        # L'opportunité est valide si le profit actuel est au moins 90% du profit original
        return current_profit >= (original_profit * 0.9)

    def update_stats(self, opportunity: Dict, trade_result: Dict):
        """Met à jour les statistiques après un trade réussi"""
        trade_data = {
            'pair': f"{opportunity['token0_symbol']}/{opportunity['token1_symbol']}",
            'profit_usdt': trade_result['profit_usdt'],
            'volume_usdt': opportunity['volume_usdt'],
            'profit_percent': opportunity['profit_percent'],
            'gas_cost_usdt': trade_result['gas_cost_usdt'],
            'net_profit_usdt': trade_result['profit_usdt'] - trade_result['gas_cost_usdt']
        }
        
        self.stats.add_trade(trade_data)

    async def get_eth_price_in_usdt(self) -> float:
        """Récupère le prix actuel de l'ETH en USDT"""
        # Implémentation de la récupération du prix ETH/USDT
        # Utilisation d'une paire de référence sur Uniswap ou Sushiswap
        pass