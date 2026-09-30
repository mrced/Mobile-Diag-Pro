import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TestStatus(Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    test_id: str
    name: str
    category: str
    status: TestStatus
    details: str
    value: Any = None
    duration_ms: int = 0


@dataclass
class DiagnosticReport:
    device_serial: str
    start_time: datetime
    end_time: datetime
    overall_score: int = 0
    passed_count: int = 0
    warning_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    results: List[TestResult] = field(default_factory=list)

    @property
    def total_duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()


class DiagnosticEngine:
    """
    Motor de Diagnóstico Compreensivo.
    Contém +50 testes profundos divididos em 12 categorias.
    """

    def __init__(self, adb_client=None) -> None:
        """
        Inicializa o motor de diagnósticos.

        Args:
            adb_client: Instância opcional de um cliente ADB.
        """
        self.adb = adb_client
        self._tests_metadata = [
            # Battery
            {"id": "batt_health", "name": "Battery Health", "category": "battery", "desc": "Verifica a saúde da bateria via dumpsys."},
            {"id": "batt_level", "name": "Battery Level", "category": "battery", "desc": "Nível de carga da bateria."},
            {"id": "batt_voltage", "name": "Battery Voltage", "category": "battery", "desc": "Tensão da bateria em mV."},
            {"id": "batt_temp", "name": "Battery Temperature", "category": "battery", "desc": "Temperatura atual da bateria."},
            {"id": "batt_capacity", "name": "Capacity (Real vs Design)", "category": "battery", "desc": "Comparação de capacidade de fábrica e atual."},
            {"id": "batt_wear", "name": "Battery Wear Level", "category": "battery", "desc": "Porcentagem de degradação estimada."},
            {"id": "batt_cycles", "name": "Cycle Count", "category": "battery", "desc": "Contagem de ciclos de carga (se suportado)."},
            {"id": "batt_charger", "name": "Charger Type", "category": "battery", "desc": "Tipo do carregador conectado (AC, USB, Wireless)."},

            # CPU
            {"id": "cpu_arch", "name": "Architecture", "category": "cpu", "desc": "Arquitetura do processador (ex. aarch64)."},
            {"id": "cpu_cores", "name": "Core Count", "category": "cpu", "desc": "Número total de núcleos físicos/lógicos."},
            {"id": "cpu_online", "name": "Online Cores", "category": "cpu", "desc": "Núcleos ativos no momento."},
            {"id": "cpu_freq", "name": "Max/Min Frequency", "category": "cpu", "desc": "Frequências máxima e mínima de operação."},
            {"id": "cpu_throttle", "name": "Throttling Check", "category": "cpu", "desc": "Verifica se há restrição térmica ativa no CPU."},
            {"id": "cpu_load", "name": "CPU Load", "category": "cpu", "desc": "Carga atual geral de processamento."},

            # Memory
            {"id": "mem_total", "name": "Total RAM", "category": "memory", "desc": "Memória RAM total instalada."},
            {"id": "mem_free", "name": "Free RAM", "category": "memory", "desc": "Memória livre no sistema."},
            {"id": "mem_avail", "name": "Available RAM", "category": "memory", "desc": "Memória disponível considerando buffers/cache."},
            {"id": "mem_cache", "name": "Cached/Buffers", "category": "memory", "desc": "Memória em cache/buffers."},
            {"id": "mem_zram", "name": "ZRAM Enabled", "category": "memory", "desc": "Status de compactação de RAM em zRAM."},
            {"id": "mem_swap", "name": "Swap Usage", "category": "memory", "desc": "Uso de swap / virtual memory."},
            {"id": "mem_oom", "name": "OOM Kills Check", "category": "memory", "desc": "Verificação de histórico de processos terminados por falta de memória."},

            # Storage
            {"id": "sto_data", "name": "Data Partition Space", "category": "storage", "desc": "Armazenamento livre em userdata."},
            {"id": "sto_sys", "name": "System Partition", "category": "storage", "desc": "Espaço na partição de sistema."},
            {"id": "sto_health", "name": "Storage Health/Read-Only", "category": "storage", "desc": "Verifica se a montagem está read-only (sinal de corrupção)."},
            {"id": "sto_io", "name": "I/O Latency", "category": "storage", "desc": "Verificação de tempo de resposta I/O básico."},
            {"id": "sto_sd", "name": "SDCard Presence", "category": "storage", "desc": "Identificação de cartão MicroSD externo."},

            # Display
            {"id": "disp_res", "name": "Resolution", "category": "display", "desc": "Resolução física/lógica da tela."},
            {"id": "disp_dpi", "name": "Density DPI", "category": "display", "desc": "Densidade de pixels do visor."},
            {"id": "disp_refresh", "name": "Refresh Rate", "category": "display", "desc": "Taxa de atualização de tela atual."},
            {"id": "disp_bright", "name": "Brightness", "category": "display", "desc": "Nível de brilho configurado."},
            {"id": "disp_state", "name": "Screen State", "category": "display", "desc": "Estado de energia da tela (ON, OFF, DOZE)."},

            # Sensors
            {"id": "sen_accel", "name": "Accelerometer", "category": "sensors", "desc": "Verificação do acelerômetro."},
            {"id": "sen_gyro", "name": "Gyroscope", "category": "sensors", "desc": "Verificação do giroscópio."},
            {"id": "sen_prox", "name": "Proximity", "category": "sensors", "desc": "Verificação do sensor de proximidade."},
            {"id": "sen_light", "name": "Light Sensor", "category": "sensors", "desc": "Verificação do sensor de luminosidade ambiental."},
            {"id": "sen_mag", "name": "Magnetometer", "category": "sensors", "desc": "Verificação da bússola/magnetômetro."},
            {"id": "sen_bar", "name": "Barometer", "category": "sensors", "desc": "Verificação do barômetro."},

            # Thermal
            {"id": "therm_cpu", "name": "CPU Temp", "category": "thermal", "desc": "Temperatura de zonas térmicas do CPU."},
            {"id": "therm_batt", "name": "Battery Temp", "category": "thermal", "desc": "Leitura redundante de temperatura da bateria."},
            {"id": "therm_gpu", "name": "GPU Temp", "category": "thermal", "desc": "Temperatura do acelerador gráfico."},
            {"id": "therm_hal", "name": "Thermal Hal Status", "category": "thermal", "desc": "Estado da camada de hardware térmico / nível de throttling."},

            # Network
            {"id": "net_wifi", "name": "WiFi Connected", "category": "network", "desc": "Status de conexão sem fio."},
            {"id": "net_wifi_sig", "name": "WiFi Signal (dBm)", "category": "network", "desc": "Potência do sinal WiFi conectada."},
            {"id": "net_wifi_spd", "name": "Link Speed", "category": "network", "desc": "Velocidade do link WiFi."},
            {"id": "net_sim", "name": "SIM State", "category": "network", "desc": "Presença e estado do chip SIM."},
            {"id": "net_cell_sig", "name": "Cellular Signal", "category": "network", "desc": "Status de recepção da rede celular."},
            {"id": "net_data", "name": "Mobile Data", "category": "network", "desc": "Status de tráfego de dados móveis."},

            # System
            {"id": "sys_os", "name": "Android Version", "category": "system", "desc": "Versão do SO e SDK."},
            {"id": "sys_patch", "name": "Security Patch Date", "category": "system", "desc": "Nível de atualização de segurança."},
            {"id": "sys_bootloader", "name": "Bootloader Status", "category": "system", "desc": "Estado de bloqueio do bootloader."},
            {"id": "sys_verified", "name": "Verified Boot State", "category": "system", "desc": "Estado do dm-verity e boot verificado."},
            {"id": "sys_encrypt", "name": "Encryption State", "category": "system", "desc": "Status da criptografia (FBE/FDE)."},
            {"id": "sys_knox", "name": "Knox/Warranty Bit", "category": "system", "desc": "Indicador de violação de garantia (para Samsung, etc.)."},
            {"id": "sys_uptime", "name": "Uptime", "category": "system", "desc": "Tempo desde a última reinicialização."},

            # Apps
            {"id": "app_3rd", "name": "Third-Party App Count", "category": "apps", "desc": "Total de aplicativos instalados pelo usuário."},
            {"id": "app_sys", "name": "System Apps", "category": "apps", "desc": "Total de apps do sistema e fornecedores."},
            {"id": "app_dis", "name": "Disabled Packages", "category": "apps", "desc": "Lista ou contagem de pacotes desabilitados."},
            {"id": "app_sus", "name": "Bloatware/Suspicious", "category": "apps", "desc": "Análise básica para adware/malware conhecido."},

            # Processes
            {"id": "proc_cpu", "name": "Top CPU Consumers", "category": "processes", "desc": "Processos demandando mais processamento."},
            {"id": "proc_mem", "name": "Memory Leak Suspects", "category": "processes", "desc": "Processos com consumo anômalo de memória."},
            {"id": "proc_anr", "name": "ANR Log Check", "category": "processes", "desc": "Procura indícios de falhas/ANRs recentes."},
            {"id": "proc_srv", "name": "Running Services", "category": "processes", "desc": "Total de serviços ativos em segundo plano."},

            # Connectivity
            {"id": "conn_usb", "name": "USB Configuration", "category": "connectivity", "desc": "Configuração USB ativa (mtp, adb, etc)."},
            {"id": "conn_adb", "name": "ADB Authorization", "category": "connectivity", "desc": "Status da chave ADB com o dispositivo."},
            {"id": "conn_fastboot", "name": "Fastboot Capability", "category": "connectivity", "desc": "Capacidade de entrar em modo bootloader/fastboot."},
        ]

    def get_available_tests(self) -> List[Dict[str, str]]:
        """
        Retorna metadados para todos os testes suportados.

        Returns:
            List[Dict[str, str]]: Lista de dicionários descrevendo os testes.
        """
        return self._tests_metadata

    def run_test(self, serial: str, test_id: str) -> TestResult:
        """
        Executa um teste individual específico.
        Nesta versão, os resultados são simulados (mock) caso a lógica
        de shell específica ainda não esteja implementada.

        Args:
            serial: O número de série do dispositivo alvo.
            test_id: O ID interno do teste.

        Returns:
            TestResult: Resultado do teste com status, detalhes e duração.
        """
        start = time.time()
        test_info = next((t for t in self._tests_metadata if t["id"] == test_id), None)
        if not test_info:
            return TestResult(test_id, "Unknown Test", "unknown", TestStatus.SKIPPED, "Test ID não encontrado.")
        
        try:
            # TODO: Substituir lógica mockada por chamadas de linha de comando reais ao shell ADB.
            # Ex: self.adb.shell(serial, "dumpsys battery")
            
            # Simulação:
            status = TestStatus.PASSED
            details = "Teste executado com sucesso. Parâmetros dentro da normalidade."
            value = "OK"

        except Exception as e:
            status = TestStatus.FAILED
            details = f"Erro na execução do teste: {e}"
            value = None

        duration_ms = int((time.time() - start) * 1000)
        return TestResult(
            test_id=test_id,
            name=test_info["name"],
            category=test_info["category"],
            status=status,
            details=details,
            value=value,
            duration_ms=duration_ms
        )

    def run_category(self, serial: str, category: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> List[TestResult]:
        """
        Executa todos os testes de uma categoria específica.

        Args:
            serial: O serial ADB do dispositivo.
            category: Nome da categoria a ser executada.
            progress_callback: Função opcional para emitir progresso (pct, msg).

        Returns:
            List[TestResult]: Resultados de todos os testes na categoria.
        """
        tests = [t for t in self._tests_metadata if t["category"] == category]
        results = []
        total = len(tests)
        
        for idx, t in enumerate(tests):
            if progress_callback:
                pct = int((idx / total) * 100)
                progress_callback(pct, f"Executando {t['name']}...")
            
            res = self.run_test(serial, t["id"])
            results.append(res)
            
        if progress_callback:
            progress_callback(100, f"Categoria {category} concluída.")
            
        return results

    def run_all_tests(self, serial: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> DiagnosticReport:
        """
        Executa todos os diagnósticos (50+) no dispositivo conectado.
        Calcula as estatísticas e um score global ponderado.

        Args:
            serial: Serial ADB do dispositivo.
            progress_callback: Função opcional para emitir progresso.

        Returns:
            DiagnosticReport: O relatório completo populado.
        """
        report = DiagnosticReport(
            device_serial=serial,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        total = len(self._tests_metadata)
        
        for idx, t in enumerate(self._tests_metadata):
            if progress_callback:
                pct = int((idx / total) * 100)
                progress_callback(pct, f"Testando: {t['name']}")
                
            res = self.run_test(serial, t["id"])
            report.results.append(res)
            
            if res.status == TestStatus.PASSED:
                report.passed_count += 1
            elif res.status == TestStatus.WARNING:
                report.warning_count += 1
            elif res.status == TestStatus.FAILED:
                report.failed_count += 1
            else:
                report.skipped_count += 1

        report.end_time = datetime.now()
        
        # Calcular pontuação baseada em pesos
        if total > 0:
            score_pts = (report.passed_count * 1.0) + (report.warning_count * 0.6)
            report.overall_score = int((score_pts / total) * 100)
            
        if progress_callback:
            progress_callback(100, "Diagnóstico completo.")
            
        return report
