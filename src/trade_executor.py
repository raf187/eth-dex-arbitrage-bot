from web3 import Web3
from typing import Dict
import json

class TradeExecutor:
    def __init__(self, w3, private_key: str):
        self.w3 = w3
        self.account = self.w3.eth.account.from_key(private_key)
        
        # ABIs nécessaires pour les interactions avec les smart contracts
        self.router_abi = json.loads('''[
            {"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}
        ]''')
        
        # Adresses des routeurs
        self.UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
        self.SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
        
    async def execute_arbitrage(self, opportunity: Dict) -> Dict:
        """Exécute un arbitrage entre Uniswap et Sushiswap"""
        try:
            # Configuration des contrats
            uni_router = self.w3.eth.contract(
                address=self.UNISWAP_ROUTER,
                abi=self.router_abi
            )
            sushi_router = self.w3.eth.contract(
                address=self.SUSHISWAP_ROUTER,
                abi=self.router_abi
            )
            
            # Préparation des paramètres de transaction
            amount_in = opportunity['optimal_amount']
            min_amount_out = int(amount_in * 1.001)  # 0.1% de slippage minimum
            deadline = self.w3.eth.get_block('latest').timestamp + 300  # 5 minutes
            path = [opportunity['token0'], opportunity['token1']]
            
            # Sélection du routeur pour l'achat et la vente
            buy_router = uni_router if opportunity['buy_on_uni'] else sushi_router
            sell_router = sushi_router if opportunity['buy_on_uni'] else uni_router
            
            # Construction des transactions
            buy_tx = buy_router.functions.swapExactTokensForTokens(
                amount_in,
                min_amount_out,
                path,
                self.account.address,
                deadline
            )
            
            # Estimation du gas
            gas_estimate = buy_tx.estimate_gas({'from': self.account.address})
            gas_price = self.w3.eth.gas_price
            
            # Préparation de la transaction
            transaction = {
                'from': self.account.address,
                'gas': int(gas_estimate * 1.2),  # +20% pour la sécurité
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            }
            
            # Signature et envoi de la transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                buy_tx.build_transaction(transaction),
                self.account.key
            )
            
            # Envoi de la transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Vérification du succès
            if receipt['status'] == 1:
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'gas_price': gas_price,
                    'profit_usdt': opportunity['expected_profit_usdt']
                }
            else:
                return {
                    'success': False,
                    'error': 'Transaction failed',
                    'tx_hash': tx_hash.hex()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def approve_token(self, token_address: str, spender_address: str):
        """Approuve un token pour le trading"""
        token_abi = json.loads('''[
            {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
        ]''')
        
        token_contract = self.w3.eth.contract(address=token_address, abi=token_abi)
        
        # Approve pour un montant maximum
        max_amount = Web3.to_wei(2**64 - 1, 'ether')
        
        tx = token_contract.functions.approve(
            spender_address,
            max_amount
        ).build_transaction({
            'from': self.account.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)