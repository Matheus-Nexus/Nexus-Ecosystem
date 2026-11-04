"""
NEXUS — Ponto de Entrada Principal.
Suporta execução local (python main.py) e PaaS (uvicorn main:app).
"""

import asyncio
import sys
import os

# Garante que o diretório do projeto esteja no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'nexus')))

from nexus.core import NexusCore
from nexus.bank import NexusBank
from nexus.runtime import NexusRuntime
from nexus.api import NexusAPI
from nexus.cli import NexusCLI

# Variáveis globais para o PaaS
_runtime_instance = None
_api_instance = None

def _init_nexus():
    """Inicializa o NEXUS e retorna as instâncias."""
    global _runtime_instance, _api_instance
    
    if _runtime_instance:
        return _runtime_instance, _api_instance
        
    bank = NexusBank(initial_balance=1000.0)
    core = NexusCore(temperature=0.7, bank=bank)
    runtime = NexusRuntime(core=core, bank=bank)
    api = NexusAPI(runtime)
    
    if not core.get_memory("system_version"):
        core.set_memory("system_version", "1.1.0")
        core.set_memory("founding_principle", "Autodesenvolvimento contínuo e interoperabilidade.")
        
    _runtime_instance = runtime
    _api_instance = api
    return runtime, api

# Cria o app FastAPI global para o uvicorn
# Se o NEXUS estiver rodando localmente, o main() abaixo será usado
# Se estiver em PaaS, o uvicorn usará este 'app'
app = _api_instance._app if _api_instance else None

# Se o arquivo for executado diretamente (python main.py)
if __name__ == "__main__":
    async def main():
        print("🚀 Inicializando NEXUS Ecosystem (Modo Local)...")
        runtime, api = _init_nexus()
        
        print("✅ NEXUS pronto para operação.")
        print("🌐 Dashboard disponível em: http://localhost:8000")
        print("⌨️  CLI disponível no terminal")
        print("⏳ Iniciando loop 24/7... (Ctrl+C para parar)")
        
        api_task = asyncio.create_task(api.run())
        cli_task = asyncio.create_task(NexusCLI(runtime).start())
        runtime_task = asyncio.create_task(runtime.start())
        
        try:
            await asyncio.gather(api_task, cli_task, runtime_task)
        finally:
            runtime._bank.close()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 NEXUS parado pelo usuário.")

# Se o arquivo for importado pelo uvicorn (PaaS)
else:
    # Garante que o runtime esteja rodando em background
    async def _start_background_runtime():
        runtime, _ = _init_nexus()
        await runtime.start()
    
    # Inicia o runtime em background quando o app é carregado
    asyncio.get_event_loop().create_task(_start_background_runtime())
