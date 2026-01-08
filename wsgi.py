import sys
import os

# === CONFIGURAÇÃO StockFlow ===
APP_PATH = '/home/deltadevs/stockflow'

# Adiciona ao path
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)

# Muda diretório
os.chdir(APP_PATH)

# Importa a aplicação
from app import app as application

print("✓ StockFlow carregado com sucesso!")