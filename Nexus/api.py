# No nexus/api.py, certifique-se de que a classe NexusAPI tenha:

class NexusAPI:
    def __init__(self, runtime: "NexusRuntime"):
        self._runtime = runtime
        self._core = runtime._core
        self._bank = runtime._bank
        self._app = FastAPI(title="NEXUS Control Plane", version="1.0.0")
        self._connections: List[WebSocket] = []
        self._setup_routes()
        
    # ... (resto do código)
