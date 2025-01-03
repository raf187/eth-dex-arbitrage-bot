from web3 import Web3
from dotenv import load_dotenv
import os

class Web3Client:
    def __init__(self):
        load_dotenv()
        self.alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
        self.w3 = Web3(Web3.HTTPProvider(self.alchemy_url))
        
    def check_connection(self):
        """Vérifie la connexion à Ethereum"""
        return self.w3.is_connected()
        
    def get_eth_balance(self, address):
        """Récupère le solde ETH d'une adresse"""
        return self.w3.eth.get_balance(address)
        
    async def get_gas_price(self):
        """Récupère le prix du gas actuel"""
        return await self.w3.eth.gas_price

    async def estimate_gas(self, transaction):
        """Estime le gas nécessaire pour une transaction"""
        return await self.w3.eth.estimate_gas(transaction)