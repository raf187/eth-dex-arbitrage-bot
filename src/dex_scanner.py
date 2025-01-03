from web3 import Web3
from typing import List, Tuple, Dict
import json

# ABIs nécessaires
FACTORY_ABI = json.loads('''[
    {"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

PAIR_ABI = json.loads('''[
    {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

class DexScanner:
    def __init__(self, w3, uniswap_factory_address: str, sushiswap_factory_address: str):
        self.w3 = w3
        self.uniswap_factory = w3.eth.contract(address=uniswap_factory_address, abi=FACTORY_ABI)
        self.sushiswap_factory = w3.eth.contract(address=sushiswap_factory_address, abi=FACTORY_ABI)
        self.known_tokens: Dict[str, Dict] = {}
        self.common_pairs: List[Tuple[str, str]] = []

    async def get_token_info(self, token_address: str) -> Dict:
        """Récupère les informations d'un token (symbole, décimales)"""
        if token_address in self.known_tokens:
            return self.known_tokens[token_address]

        token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        try:
            symbol = await token_contract.functions.symbol().call()
            decimals = await token_contract.functions.decimals().call()
            token_info = {"symbol": symbol, "decimals": decimals}
            self.known_tokens[token_address] = token_info
            return token_info
        except Exception as e:
            print(f"Erreur lors de la récupération des infos du token {token_address}: {e}")
            return None

    async def get_pair_tokens(self, pair_address: str) -> Tuple[str, str]:
        """Récupère les adresses des tokens d'une paire"""
        pair_contract = self.w3.eth.contract(address=pair_address, abi=PAIR_ABI)
        token0 = await pair_contract.functions.token0().call()
        token1 = await pair_contract.functions.token1().call()
        return token0, token1

    async def scan_dex_pairs(self, max_pairs: int = 1000) -> List[Tuple[str, str]]:
        """Scan les paires communes entre Uniswap et Sushiswap"""
        uni_pairs = set()
        sushi_pairs = set()

        # Scan Uniswap pairs
        uni_length = min(await self.uniswap_factory.functions.allPairsLength().call(), max_pairs)
        for i in range(uni_length):
            pair_address = await self.uniswap_factory.functions.allPairs(i).call()
            tokens = await self.get_pair_tokens(pair_address)
            uni_pairs.add(tuple(sorted([tokens[0], tokens[1]])))

        # Scan Sushiswap pairs
        sushi_length = min(await self.sushiswap_factory.functions.allPairsLength().call(), max_pairs)
        for i in range(sushi_length):
            pair_address = await self.sushiswap_factory.functions.allPairs(i).call()
            tokens = await self.get_pair_tokens(pair_address)
            sushi_pairs.add(tuple(sorted([tokens[0], tokens[1]])))

        # Find common pairs
        self.common_pairs = list(uni_pairs.intersection(sushi_pairs))
        return self.common_pairs

    async def get_reserves(self, pair_address: str) -> Tuple[int, int]:
        """Récupère les réserves d'une paire"""
        pair_contract = self.w3.eth.contract(address=pair_address, abi=PAIR_ABI)
        reserves = await pair_contract.functions.getReserves().call()
        return reserves[0], reserves[1]