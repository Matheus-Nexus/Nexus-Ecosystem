"""
NEXUS BANK — Tokenomics Engine.
Gerencia o ciclo de vida dos tokens: Mint, Burn, Reservas e Abundância.
"""

import sqlite3
import json
import time
import os
from typing import Dict, Any, Optional, List

DB_PATH = "nexus_state.db"

class NexusBank:
    """
    Banco de dados do NEXUS com lógica de Tokenomics.
    """
    
    def __init__(self, initial_balance: float = 1000.0, db_path: str = DB_PATH):
        self._db_path = db_path
        self._init_db(initial_balance)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        
        # Parâmetros de Tokenomics
        self._mint_base = 1.0  # Base de mineração por ciclo
        self._burn_rate = 0.1  # Custo base de operação
        self._efficiency_bonus = 0.5 # Bônus por eficiência

    def _init_db(self, initial_balance: float):
        """Inicializa o esquema do banco de dados."""
        schema = """
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value REAL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            entry_id TEXT PRIMARY KEY,
            operation_id TEXT,
            event_type TEXT,
            metadata TEXT,
            timestamp REAL
        );

        CREATE TABLE IF NOT EXISTS memory (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        
        CREATE TABLE IF NOT EXISTS token_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            type TEXT, -- MINT, BURN, TRANSFER
            amount REAL,
            reason TEXT,
            agent_id TEXT
        );
        """
        self._conn.executescript(schema)
        
        # Inicializa saldo se for a primeira vez
        self._conn.execute("INSERT OR IGNORE INTO state (key, value) VALUES ('balance', ?)", (initial_balance,))
        self._conn.commit()

    # --- MÉTODOS DE SALDO ---

    def get_balance(self) -> float:
        """Recupera o saldo atual."""
        cursor = self._conn.execute("SELECT value FROM state WHERE key='balance'")
        row = cursor.fetchone()
        return row['value'] if row else 0.0

    def _adjust_balance(self, amount: float, type: str, reason: str, agent_id: str = "SYSTEM"):
        """
        Ajusta o saldo e registra no ledger.
        """
        self._conn.execute("UPDATE state SET value = value + ? WHERE key='balance'", (amount,))
        self._conn.execute(
            "INSERT INTO token_ledger (timestamp, type, amount, reason, agent_id) VALUES (?, ?, ?, ?, ?)",
            (time.time(), type, amount, reason, agent_id)
        )
        self._conn.commit()

    def mint(self, amount: float, reason: str, agent_id: str = "SYSTEM"):
        """Minta tokens (geração de abundância)."""
        self._adjust_balance(amount, "MINT", reason, agent_id)

    def burn(self, amount: float, reason: str, agent_id: str = "SYSTEM"):
        """Queima tokens (custo de operação)."""
        self._adjust_balance(-amount, "BURN", reason, agent_id)

    # --- MÉTODOS DE AUDITORIA E MEMÓRIA (Mantidos do código anterior) ---

    def record_audit_log(self, operation_id: str, event_type: str, metadata: Dict[str, Any]) -> str:
        """Registra um evento de auditoria."""
        entry_id = f"AUDIT_{int(time.time() * 1000)}"
        self._conn.execute(
            "INSERT INTO audit_log (entry_id, operation_id, event_type, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
            (entry_id, operation_id, event_type, json.dumps(metadata), time.time())
        )
        self._conn.commit()
        return entry_id

    def get_audit_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna os últimos eventos de auditoria."""
        cursor = self._conn.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [{"entry_id": r['entry_id'], "operation_id": r['operation_id'], "event_type": r['event_type'], "metadata": json.loads(r['metadata']), "timestamp": r['timestamp']} for r in rows]

    def set_memory(self, key: str, value: Any):
        """Salva um valor na memória persistente."""
        value_str = json.dumps(value)
        self._conn.execute("INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)", (key, value_str))
        self._conn.commit()

    def get_memory(self, key: str, default=None):
        """Recupera um valor da memória persistente."""
        cursor = self._conn.execute("SELECT value FROM memory WHERE key=?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                return row['value']
        return default

    def get_all_memory(self) -> Dict[str, Any]:
        """Recupera toda a memória persistente."""
        cursor = self._conn.execute("SELECT key, value FROM memory")
        rows = cursor.fetchall()
        memory = {}
        for row in rows:
            try:
                memory[row['key']] = json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                memory[row['key']] = row['value']
        return memory

    def backup_database(self, backup_dir: str = "backups") -> str:
        """Cria um backup do banco de dados."""
        import shutil
        from datetime import datetime
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_dir}/nexus_state_{timestamp}.db"
        shutil.copy2(self._db_path, backup_filename)
        
        # Remove backups antigos
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("nexus_state_") and f.endswith(".db")])
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(old_backup)
        return backup_filename

    def close(self):
        """Fecha a conexão com o banco."""
        if self._conn:
            self._conn.close()
