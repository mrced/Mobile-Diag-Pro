import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class WorkerSignals(QObject):
    """
    Sinais para o trabalhador de execução de comandos (Worker).
    Fornece comunicação segura entre threads para a GUI.
    """
    started = Signal()
    finished = Signal()
    result = Signal(object)
    error = Signal(str)
    progress = Signal(int, str)  # porcentagem, mensagem de status


class Worker(QRunnable):
    """
    Trabalhador executável assíncrono para o QThreadPool.
    """
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """
        Inicializa o trabalhador.

        Args:
            fn: A função a ser executada na thread separada.
            args: Argumentos posicionais para a função.
            kwargs: Argumentos nomeados para a função.
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        """
        Executa a função configurada, emitindo os sinais apropriados de início,
        resultado, erro e término.
        """
        self.signals.started.emit()
        try:
            # Se a função esperar um callback de progresso e fornecermos suporte para isso,
            # ele poderia ser injetado. Aqui executamos diretamente.
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            error_msg = f"Erro na execução: {str(e)}\n{traceback.format_exc()}"
            self.signals.error.emit(error_msg)
        finally:
            self.signals.finished.emit()


class CommandExecutor(QObject):
    """
    Executor de comandos assíncronos (Singleton) gerenciando uma pool de threads.
    Facilita a execução de comandos em background sem travar a interface gráfica.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CommandExecutor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """
        Inicializa o pool global de threads, garantindo apenas uma inicialização.
        """
        if self._initialized:
            return
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self._initialized = True

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> WorkerSignals:
        """
        Submete uma função para execução assíncrona no pool de threads.

        Args:
            fn: A função a ser executada.
            args: Argumentos posicionais da função.
            kwargs: Argumentos nomeados da função.

        Returns:
            WorkerSignals: Sinais (started, finished, result, error, progress)
                           para conectar handlers na thread da GUI.
        """
        worker = Worker(fn, *args, **kwargs)
        self.pool.start(worker)
        return worker.signals

    def set_max_threads(self, count: int) -> None:
        """
        Define o número máximo de threads ativas simultaneamente no pool.

        Args:
            count: Número máximo de threads.
        """
        self.pool.setMaxThreadCount(count)
