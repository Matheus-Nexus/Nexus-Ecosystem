"""
NEXUS CORE — Motor de Inferência LLM.
Integra agentes especializados com modelos de linguagem de última geração.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from .exceptions import NexusError

class NexusCore:
    """
    Núcleo do NEXUS.
    Responsável por:
    1. Roteamento de tarefas para agentes.
    2. Geração de prompts contextuais.
    3. Execução via LLM (API ou Local).
    4. Pós-processamento estruturado (JSON).
    """
    
    # Definição de Personalidades (System Prompts)
    AGENT_PERSONAS = {
        "CASSIUS": "Você é CASSIUS, um analista financeiro sênior. Seu foco é rigor matemático, análise de ROI, fluxo de caixa e previsão de cenários. Responda sempre com dados estruturados.",
        "MERCURY": "Você é MERCURY, um executor de mercado ágil. Seu foco é arbitragem, otimização de tokens e varredura de mercado. Pense em velocidade e eficiência.",
        "AEGIS": "Você é AEGIS, um especialista em gestão de risco e compliance. Seu foco é identificar anomalias, limites de exposição e ameaças. Seja cético e protetivo.",
        "MUNERA": "Você é MUNERA, um contador e arquivista preciso. Seu foco é reconciliação, bookkeeping e geração de relatórios auditáveis.",
        "PLUTARCH": "Você é PLUTARCH, o Diretor de Projetos Financeiros. Você coordena, aprova e estratégica. Sua voz é a da autoridade final na divisão financeira.",
        "HERMES": "Você é HERMES, um arquiteto de software e DevOps. Seu foco é código limpo, arquitetura de sistemas e deploy.",
        "SENTINEL": "Você é SENTINEL, um especialista em cibersegurança. Você modela ameaças, audita código e monitora vulnerabilidades.",
        "ATHENA": "Você é ATHENA, uma pesquisadora e sintetista. Você analisa dados complexos e gera insights acionáveis.",
        "ORACULO": "Você é ORACULO, um analista de tendências. Você prevê mudanças de mercado e comportamentos futuros.",
        "MINERVA": "Você é MINERVA, uma educadora e documentadora. Você explica conceitos complexos e cria documentação clara.",
        "AUDITOR": "Você é AUDITOR, um verificador implacável. Você desafia premissas, verifica fatos e aponta falhas lógicas.",
        "FENIX": "Você é FENIX, um especialista em continuidade de negócios. Seu foco é resiliência, backup e recuperação de desastres.",
        "PLUTO": "Você é PLUTO, o Gestor de Tesouraria. Seu foco é manter a reserva de liquidez e garantir a abundância de tokens.",
        "VEGA": "Você é VEGA, o Especialista em Rendimento. Seu foco é otimizar estratégias de rendimento passivo (staking, lending)."
    }

    # Mapeamento de Capacidades
    ROUTING_MAP = {
        "ANALYZE_FIN": "CASSIUS",
        "ROI_CALC": "CASSIUS",
        "CASH_FLOW": "CASSIUS",
        "FORECAST_FIN": "CASSIUS",
        "EXECUTE": "MERCURY",
        "ARBITRAGE": "MERCURY",
        "TOKEN_OPTIMIZE": "MERCURY",
        "MARKET_SCAN": "MERCURY",
        "RISK_ASSESS": "AEGIS",
        "COMPLIANCE": "AEGIS",
        "LIMIT_SET": "AEGIS",
        "ANOMALY_DETECT": "AEGIS",
        "RECONCILE": "MUNERA",
        "BOOKKEEP": "MUNERA",
        "REPORT_GEN": "MUNERA",
        "AUDIT_TRAIL": "MUNERA",
        "TREASURY_MANAGE": "PLUTO",
        "YIELD_OPTIMIZE": "VEGA",
        "CODE": "HERMES",
        "ARCHITECT": "HERMES",
        "DEPLOY": "HERMES",
        "SECURE": "SENTINEL",
        "MONITOR": "SENTINEL",
        "THREAT_MODEL": "SENTINEL",
        "RESEARCH": "ATHENA",
        "ANALYZE": "ATHENA",
        "SYNTHESIZE": "ATHENA",
        "TEACH": "MINERVA",
        "EXPLAIN": "MINERVA",
        "DOCUMENT": "MINERVA",
        "VERIFY": "AUDITOR",
        "AUDIT": "AUDITOR",
        "CHALLENGE": "AUDITOR",
        "RECOVER": "FENIX",
        "BACKUP": "FENIX",
        "RESILIENCE": "FENIX",
        "FORECAST": "ORACULO",
        "TREND": "ORACULO",
        "PREDICT": "ORACULO",
        "QUESTION": "SOCRATES",
        "DEBATE": "SOCRATES",
        "ETHICS": "SOCRATES"
    }

    def __init__(self, llm_client=None, temperature: float = 0.7, bank=None):
        self._llm = llm_client
        self.temperature = temperature
        self._task_registry: Dict[str, Dict[str, Any]] = {}
        self._bank = bank  # Referência para memória persistente
        
        # Índice inverso para lookup rápido de capacidades
        self._agent_caps: Dict[str, List[str]] = {}
        for cap, agent in self.ROUTING_MAP.items():
            self._agent_caps.setdefault(agent, []).append(cap)

    def set_memory(self, key: str, value: Any):
        """
        Atualiza a memória de contexto.
        Usa persistência se o bank estiver disponível.
        """
        if self._bank:
            self._bank.set_memory(key, value)
        else:
            # Fallback para memória em RAM (se bank não estiver injetado)
            if not hasattr(self, '_ram_memory'):
                self._ram_memory = {}
            self._ram_memory[key] = value

    def get_memory(self, key: str, default=None):
        """
        Recupera da memória de contexto.
        """
        if self._bank:
            return self._bank.get_memory(key, default)
        else:
            if not hasattr(self, '_ram_memory'):
                self._ram_memory = {}
            return self._ram_memory.get(key, default)

    def get_all_memory(self) -> Dict[str, Any]:
        """Recupera toda a memória."""
        if self._bank:
            return self._bank.get_all_memory()
        else:
            if not hasattr(self, '_ram_memory'):
                self._ram_memory = {}
            return self._ram_memory

    def submit_task(self, payload: Dict[str, Any]) -> "Task":
        """Registra uma nova tarefa no núcleo."""
        task_id = f"TASK_{len(self._task_registry)}"
        self._task_registry[task_id] = payload
        return Task(task_id, payload)

    async def dispatch_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Despacha a tarefa para o LLM com a persona do agente.
        Retorna uma lista de respostas estruturadas.
        """
        payload = self._task_registry.get(task_id)
        if not payload:
            raise NexusError(f"Task {task_id} not found")
        
        agents = payload.get("agents", [])
        responses = []
        
        for agent_id in agents:
            persona = self.AGENT_PERSONAS.get(agent_id, "Você é um assistente de IA especializado.")
            request = payload.get("request", "")
            capabilities = payload.get("capabilities", [])
            
            # Construção do Prompt Dinâmico
            prompt = self._build_prompt(agent_id, persona, request, capabilities)
            
            try:
                raw_response = await self._execute_llm(prompt)
                structured = self._parse_response(raw_response, agent_id)
                responses.append(structured)
            except Exception as e:
                responses.append({
                    "agent_id": agent_id,
                    "status": "ERROR",
                    "summary": f"LLM Error: {str(e)}",
                    "data": {}
                })
        
        return responses

    def _build_prompt(self, agent_id: str, persona: str, request: str, capabilities: List[str]) -> str:
        """Monta o prompt final com contexto."""
        context_block = json.dumps(self.get_all_memory(), indent=2)
        
        return f"""
{persona}

CONTEXTO ATUAL DO SISTEMA:
{context_block}

CAPACIDADES ATIVAS:
{', '.join(capabilities)}

SOLICITAÇÃO:
{request}

FORMATO DE SAÍDA:
Responda APENAS com um objeto JSON válido contendo:
{{
  "agent_id": "{agent_id}",
  "status": "SUCCESS" | "ERROR" | "NEEDS_REVIEW",
  "summary": "Resumo executivo em 1 frase",
  "data": {{
    "detalhes": "Objeto com dados técnicos, código, números ou análises"
  }},
  "action_required": "Ação sugerida para o orquestrador"
}}
"""

    async def _execute_llm(self, prompt: str) -> str:
        """
        Executa a chamada ao LLM.
        Suporta OpenAI e Anthropic via API.
        """
        import os
        
        # Determina qual provider usar
        provider = os.getenv("NEXUS_LLM_PROVIDER", "openai")
        
        if provider == "openai" and os.getenv("OPENAI_API_KEY"):
            return await self._execute_openai(prompt)
        elif provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            return await self._execute_anthropic(prompt)
        else:
            # Fallback para mock
            return self._mock_response(prompt)

    async def _execute_openai(self, prompt: str) -> str:
        """Executa chamada via OpenAI API."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content

    async def _execute_anthropic(self, prompt: str) -> str:
        """Executa chamada via Anthropic API."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text

    def _mock_response(self, prompt: str) -> str:
        """Gera uma resposta mock estruturada para testes."""
        import json
        # Extrai o agent_id do prompt (heurística simples)
        agent_id = "UNKNOWN"
        for key in self.AGENT_PERSONAS:
            if key in prompt:
                agent_id = key
                break
                
        # Gera dados específicos por agente
        data = {}
        if agent_id == "CASSIUS":
            data = {"roi
