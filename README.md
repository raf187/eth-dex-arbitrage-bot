# Bot d'Arbitrage DEX

Bot d'arbitrage entre Uniswap et Sushiswap avec interface graphique.

## Installation

1. Cloner le repository
```bash
git clone https://github.com/raf187/eth-dex-arbitrage-bot.git
cd eth-dex-arbitrage-bot
```

2. Créer et activer un environnement virtuel
```bash
python -m venv venv

# Sur Mac/Linux :
source venv/bin/activate
# Sur Windows :
# venv\Scripts\activate
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos informations
```

5. Lancer l'application
```bash
python -m src.main
```

## Fonctionnalités

- Comparaison des prix entre Uniswap et Sushiswap
- Interface graphique pour le paramétrage
- Mode automatique ou manuel
- Liste de tokens préférés
- Statistiques en temps réel
- Volume minimum : 25K USDT
- Slippage maximum : 1%
- Timeout des transactions : 4 minutes