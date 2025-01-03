from typing import Dict, Tuple
from decimal import Decimal
from web3 import Web3

class ArbitrageLogic:
    def __init__(self, min_volume_usdt: float = 25000):
        self.min_volume_usdt = min_volume_usdt
        self.USDT_DECIMALS = 6
        self.USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
        
    def calculate_price_impact(self, reserve0: int, reserve1: int, amount_in: int) -> Decimal:
        """Calcule l'impact de prix pour un montant donné"""
        k = reserve0 * reserve1
        new_reserve0 = reserve0 + amount_in
        new_reserve1 = k // new_reserve0
        price_impact = (reserve1 - new_reserve1) / reserve1
        return Decimal(str(price_impact))

    def find_arbitrage_opportunity(
        self,
        uni_reserves: Tuple[int, int],
        sushi_reserves: Tuple[int, int],
        token0_decimals: int,
        token1_decimals: int
    ) -> Dict:
        """
        Trouve et calcule les opportunités d'arbitrage entre Uniswap et Sushiswap
        """
        # Prix sur Uniswap
        uni_price = (uni_reserves[1] * 10**token0_decimals) / (uni_reserves[0] * 10**token1_decimals)
        
        # Prix sur Sushiswap
        sushi_price = (sushi_reserves[1] * 10**token0_decimals) / (sushi_reserves[0] * 10**token1_decimals)

        # Calcul de la différence de prix
        price_diff = abs(uni_price - sushi_price)
        price_diff_percent = (price_diff / min(uni_price, sushi_price)) * 100

        # Déterminer la direction de l'arbitrage
        buy_on_uni = uni_price < sushi_price
        
        # Calculer le volume optimal
        optimal_amount = self._calculate_optimal_amount(
            uni_reserves if buy_on_uni else sushi_reserves,
            sushi_reserves if buy_on_uni else uni_reserves,
            token0_decimals,
            token1_decimals
        )

        # Vérifier le volume minimum
        volume_usdt = self._calculate_volume_usdt(optimal_amount, uni_price)
        
        if volume_usdt < self.min_volume_usdt:
            return None

        return {
            "profit_percent": price_diff_percent,
            "volume_usdt": volume_usdt,
            "optimal_amount": optimal_amount,
            "buy_on_uni": buy_on_uni,
            "uni_price": uni_price,
            "sushi_price": sushi_price
        }

    def _calculate_optimal_amount(
        self,
        buy_reserves: Tuple[int, int],
        sell_reserves: Tuple[int, int],
        token0_decimals: int,
        token1_decimals: int
    ) -> int:
        """
        Calcule le montant optimal pour l'arbitrage en prenant en compte les réserves
        et l'impact de prix
        """
        # Formule simplifiée pour le calcul du montant optimal
        # Cette formule peut être améliorée en prenant en compte les frais
        k1 = buy_reserves[0] * buy_reserves[1]
        k2 = sell_reserves[0] * sell_reserves[1]
        
        # On limite le montant à 30% des réserves pour éviter trop d'impact
        max_amount = min(buy_reserves[0], sell_reserves[0]) * 3 // 10
        
        return max_amount

    def _calculate_volume_usdt(self, amount: int, token_price: float) -> float:
        """Convertit un montant de token en volume USDT"""
        return amount * token_price
