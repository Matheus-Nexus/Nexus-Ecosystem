class NexusError(Exception):
    """Exceção base para o NEXUS."""
    pass

class TaskValidationError(NexusError):
    """Lançada quando uma tarefa crítica falha ou é inválida."""
    pass

class BankError(NexusError):
    """Lançada em falhas de operação bancária."""
    pass
