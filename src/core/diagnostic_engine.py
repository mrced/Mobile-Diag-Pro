"""
Motor de Diagnóstico do Mobile-Diag-Pro.

Princípios:
  * Todo resultado vem de uma LEITURA REAL do aparelho (ADB/dumpsys/procfs/sysfs/logcat).
  * Nenhum teste é aprovado "por padrão": se o dado não pôde ser lido, o teste fica
    como SKIPPED ("não medido") e o motivo é informado.
  * Cada resultado informa o CRITÉRIO usado. "Aprovado" significa exclusivamente:
    "o valor medido está dentro do limite descrito no critério".
  * Itens apenas informativos usam o status INFO (não contam como aprovados).
  * Ao final, `analyze()` correlaciona os achados e explica as causas prováveis de
    lentidão, travamentos e demora para acender a tela.
"""
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.adb_client import ADBClient
from src.core.constants import TestStatus
from src.core.logger import get_logger

logger = get_logger(__name__)

# Pacotes/processos conhecidos por consumir recursos sem benefício claro ao usuário.
KNOWN_HEAVY: Dict[str, str] = {
    "com.miui.msa.global": "MIUI System Ads — serviço de anúncios/recomendações da Xiaomi",
    "com.miui.analytics": "MIUI Analytics — telemetria da Xiaomi",
    "com.mi.android.globalminusscreen": "App Vault — feed da tela à esquerda da home",
    "com.facebook.appmanager": "Facebook App Manager — serviço residente do Facebook",
    "com.facebook.services": "Facebook Services — serviço residente do Facebook",
    "com.facebook.system": "Facebook System — serviço residente do Facebook",
    "com.psafe.msuite": "dfndr/PSafe — 'limpador' de memória (forçam recarga de apps e gastam RAM)",
    "com.cleanmaster.mguard": "Clean Master — 'limpador' de memória",
    "com.ijinshan.kbatterydoctor": "Battery Doctor — 'otimizador' de bateria",
}

SYSTEM_PROCS = {
    "system_server", "surfaceflinger", "zygote", "zygote64", "logd", "media.codec",
    "cnss_diag", "kswapd0", "kworker", "mmc-cmdqd", "android.hardware",
}


@dataclass
class TestResult:
    test_id: str
    name: str
    category: str
    status: TestStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


@dataclass
class Finding:
    """Conclusão correlacionada: o que foi achado, por que importa e o que fazer."""
    severity: str  # 'critical' | 'warning' | 'info'
    title: str
    evidence: str
    impact: str
    action: str
    tests: List[str] = field(default_factory=list)


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
    info_count: int = 0
    results: List[TestResult] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""

    @property
    def total_duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()


def _int(txt: Any, default: int = 0) -> int:
    try:
        return int(str(txt).replace(",", "").replace(".", "").strip())
    except (ValueError, TypeError):
        return default


def _float(txt: Any, default: float = 0.0) -> float:
    try:
        return float(str(txt).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def _mb(kb: float) -> str:
    return f"{kb / 1024:.0f} MB" if kb < 1024 * 1024 else f"{kb / 1024 / 1024:.2f} GB"


class DiagnosticEngine:
    """Executa coletas reais e avalia cada teste com critério explícito."""

    COLLECT_STEPS = 22

    def __init__(self, adb_client: Optional[ADBClient] = None) -> None:
        self.adb = adb_client or ADBClient()
        self._raw: Dict[str, Optional[str]] = {}
        self._errors: Dict[str, str] = {}
        self._facts: Dict[str, Any] = {}
        self._serial: str = ""
        self._collected_at: float = 0.0

        T = self._tests_metadata = []

        def add(tid: str, name: str, cat: str, desc: str) -> None:
            T.append({"id": tid, "name": name, "category": cat, "desc": desc})

        # Memória
        add("mem_total", "Memória RAM instalada", "memory", "RAM física total do aparelho.")
        add("mem_avail", "RAM disponível", "memory", "Memória realmente utilizável sem matar apps (MemAvailable).")
        add("mem_swap", "Uso de swap/zRAM", "memory", "Quanto do swap está ocupado. Swap alto = sistema sem RAM e gastando CPU para comprimir.")
        add("mem_state", "Estado de memória do Android", "memory", "Nível de pressão de memória informado pelo próprio Android (dumpsys meminfo).")
        add("mem_bgproc", "Processos em segundo plano", "memory", "Quantidade de processos mantidos vivos na memória.")
        add("mem_lmk", "Apps encerrados por falta de memória", "memory", "Taxa de apps mortos pelo sistema (log de eventos).")
        # CPU
        add("cpu_load", "Carga de CPU", "cpu", "Uso total de CPU na janela recente + espera de I/O.")
        add("cpu_throttle", "Limite de frequência (throttling)", "cpu", "Compara a frequência máxima permitida com o máximo de hardware.")
        add("cpu_cores", "Núcleos ativos", "cpu", "Núcleos online versus total possível.")
        add("cpu_gov", "Governador de CPU", "cpu", "Política de escalonamento de frequência.")
        # Armazenamento
        add("sto_free", "Espaço livre (/data)", "storage", "Espaço livre na partição do usuário.")
        add("sto_write", "Velocidade de escrita real", "storage", "Grava 64 MB temporários e mede o tempo (arquivo é apagado em seguida).")
        add("sto_latency", "Latência de escrita do Android", "storage", "Latência medida pelo serviço diskstats do Android.")
        add("sto_mount", "Montagem da partição de dados", "storage", "Confere se /data está em leitura e escrita.")
        add("sto_break", "Composição do armazenamento", "storage", "O que ocupa o espaço (apps, fotos, vídeos, sistema).")
        # Bateria
        add("batt_level", "Nível de carga", "battery", "Percentual atual.")
        add("batt_health", "Saúde reportada pelo Android", "battery", "Código de saúde do serviço de bateria.")
        add("batt_temp", "Temperatura da bateria", "battery", "Temperatura da célula.")
        add("batt_volt", "Tensão da bateria", "battery", "Tensão atual vs. nível de carga (queda indica célula fraca).")
        add("batt_capacity", "Capacidade real estimada", "battery", "Capacidade atual estimada versus a de projeto.")
        add("batt_drain", "Consumo real vs. contabilizado", "battery", "Razão entre descarga medida e a explicada pelos apps.")
        add("batt_charge", "Fonte de energia", "battery", "Tipo e corrente máxima da fonte.")
        # Térmico
        add("therm_cpu", "Temperatura da CPU", "thermal", "Maior temperatura entre as zonas térmicas de CPU.")
        add("therm_board", "Temperatura da placa", "thermal", "Sensores da placa e do SoC.")
        add("therm_storage", "Temperatura da memória interna", "thermal", "Sensor eMMC/UFS.")
        # Display
        add("disp_wake", "Tempo para ligar/apagar a tela", "display", "Duração do broadcast de tela no system_server (log de eventos).")
        add("disp_info", "Resolução e densidade", "display", "Resolução física e DPI.")
        # Sensores
        add("sen_core", "Sensores essenciais", "sensors", "Presença de acelerômetro, giroscópio, proximidade, luz e bússola.")
        # Rede
        add("net_wifi", "Wi-Fi", "network", "Sinal e velocidade do link atual.")
        # Sistema
        add("sys_version", "Versão do sistema", "system", "Android e interface do fabricante.")
        add("sys_patch", "Patch de segurança", "system", "Idade da última atualização de segurança instalada.")
        add("sys_uptime", "Tempo ligado (uptime)", "system", "Tempo desde a última inicialização.")
        add("sys_stability", "Reinicializações e travamentos do sistema", "system", "Histórico do DropBox: boots, watchdog e reinícios.")
        add("sys_anim", "Escala de animações", "system", "Animações acima de 1x deixam o aparelho aparentemente mais lento.")
        add("sys_saver", "Economia de energia", "system", "Economia de bateria ativa limita CPU e processos.")
        add("sys_boot", "Bootloader / inicialização verificada", "system", "Estado de bloqueio e verificação do boot.")
        # Apps
        add("app_user", "Apps instalados pelo usuário", "apps", "Quantidade de apps de terceiros.")
        add("app_heavy", "Apps de terceiros mais pesados (RAM)", "apps", "Apps de terceiros com maior consumo de memória agora.")
        add("app_bloat", "Serviços residentes conhecidos por pesar", "apps", "Pacotes instalados que costumam gastar CPU/RAM em segundo plano.")
        # Processos
        add("proc_cpu", "Processos que mais usam CPU", "processes", "Maiores consumidores de CPU na janela recente.")
        add("proc_anr", "Apps que pararam de responder (ANR)", "processes", "ANRs registrados pelo sistema e quais apps os causaram.")
        add("proc_native", "Falhas nativas (tombstones)", "processes", "Crashes de baixo nível registrados.")

    # ------------------------------------------------------------------ infra
    def get_available_tests(self) -> List[Dict[str, str]]:
        return self._tests_metadata

    def _sh(self, key: str, cmd: str, timeout: float = 30.0) -> Optional[str]:
        """Executa um comando no aparelho e guarda a saída bruta. Nunca inventa dados."""
        try:
            out = self.adb.shell(self._serial, cmd, timeout=timeout)
            out = (out or "").replace("\r\n", "\n").replace("\r", "\n")
            self._raw[key] = out
            return out
        except Exception as exc:
            self._raw[key] = None
            self._errors[key] = str(exc)
            logger.warning(f"Coleta '{key}' falhou: {exc}")
            return None

    def collect(self, serial: str, progress: Optional[Callable[[int, int, str], None]] = None) -> bool:
        """Coleta TODOS os dados brutos do aparelho (a parte demorada do diagnóstico)."""
        self._serial = serial
        self._raw, self._errors, self._facts = {}, {}, {}
        steps: List[Tuple[str, str, str, float]] = [
            ("date", "Lendo data/hora do aparelho", "date '+%Y-%m-%d %H:%M:%S'", 10),
            ("props", "Lendo propriedades do sistema", "getprop", 20),
            ("meminfo", "Lendo memória (/proc/meminfo)", "cat /proc/meminfo", 15),
            ("dmeminfo", "Analisando memória por processo (dumpsys meminfo)", "dumpsys meminfo", 90),
            ("lru", "Contando processos em segundo plano", "dumpsys activity processes | grep -E 'Process LRU list'", 60),
            ("cpuinfo", "Medindo uso de CPU por processo", "dumpsys cpuinfo", 40),
            ("cpufreq", "Lendo frequências e limites da CPU",
             "for i in 0 1 2 3 4 5 6 7 8 9 10 11; do d=/sys/devices/system/cpu/cpu$i/cpufreq; "
             "[ -r $d/scaling_max_freq ] && echo \"cpu$i $(cat $d/scaling_cur_freq) $(cat $d/scaling_max_freq) "
             "$(cat $d/cpuinfo_max_freq) $(cat $d/scaling_governor)\"; done", 20),
            ("cpuonline", "Lendo núcleos ativos", "cat /sys/devices/system/cpu/online; cat /sys/devices/system/cpu/possible", 10),
            ("battery", "Lendo bateria (dumpsys battery)", "dumpsys battery", 20),
            ("bstats", "Lendo estatísticas de bateria",
             "dumpsys batterystats | grep -iE 'Estimated battery capacity|learned battery|Capacity:.*Computed drain'", 60),
            ("thermal", "Lendo zonas térmicas",
             "for i in $(seq 0 59); do t=/sys/class/thermal/thermal_zone$i; "
             "[ -r $t/type ] && echo \"$(cat $t/type) $(cat $t/temp)\"; done", 30),
            ("diskstats", "Lendo diskstats do Android",
             "dumpsys diskstats | grep -E '^(Latency|Data-Free|System-Free|File-based|App Size|Photos Size|Videos Size|Audio Size|Downloads Size|System Size|Other Size)'", 40),
            ("mounts", "Verificando montagem de /data", "grep ' /data ' /proc/mounts", 10),
            ("iotest", "Testando velocidade de escrita real (64 MB temporários)",
             "dd if=/dev/zero of=/data/local/tmp/mdp_io_test bs=1M count=64 conv=fsync 2>&1 | tail -1; "
             "rm -f /data/local/tmp/mdp_io_test", 90),
            ("events", "Lendo log de eventos do sistema (encerramentos, ANR, tela)",
             "logcat -d -b events -t 20000 2>&1 | grep -E 'am_kill|am_anr|am_crash|power_screen_broadcast_done'", 90),
            ("dropbox", "Lendo histórico de falhas (DropBox)",
             "dumpsys dropbox | grep -E ' (data_app_anr|system_app_anr|SYSTEM_TOMBSTONE|data_app_native_crash|data_app_crash|system_app_crash|system_server_crash|system_server_watchdog|SYSTEM_BOOT|SYSTEM_RESTART) \\('", 60),
            ("anr_procs", "Identificando apps que travaram (ANR)",
             "(dumpsys dropbox --print data_app_anr; dumpsys dropbox --print system_app_anr) 2>&1 | grep -E '^Process:'", 120),
            ("tomb_procs", "Identificando origem das falhas nativas",
             "dumpsys dropbox --print SYSTEM_TOMBSTONE 2>&1 | grep -E '^(Process|>>> )' | head -60", 90),
            ("pkgs_user", "Listando apps instalados", "pm list packages -3", 30),
            ("pkgs_all", "Listando pacotes do sistema", "pm list packages", 30),
            ("settings", "Lendo configurações de animação e economia",
             "echo $(settings get global window_animation_scale) $(settings get global transition_animation_scale) "
             "$(settings get global animator_duration_scale) $(settings get global low_power)", 15),
            ("misc", "Lendo Wi-Fi, sensores e tela",
             "dumpsys wifi | grep mWifiInfo | head -1; echo ===SENS; dumpsys sensorservice | grep -E '^0x.*type:'; "
             "echo ===WM; wm size; wm density; echo ===UP; cat /proc/uptime", 40),
        ]
        total = len(steps)
        ok = 0
        for i, (key, label, cmd, to) in enumerate(steps):
            if progress:
                progress(i, total, label)
            if self._sh(key, cmd, to) is not None:
                ok += 1
        self._collected_at = time.time()
        if progress:
            progress(total, total, "Coleta concluída")
        # props -> dicionário
        props: Dict[str, str] = {}
        for m in re.finditer(r"^\[([^\]]+)\]: \[(.*)\]$", self._raw.get("props") or "", re.M):
            props[m.group(1)] = m.group(2)
        self._facts["props"] = props
        return ok >= 4

    # ---------------------------------------------------------------- helpers
    def _need(self, key: str) -> str:
        v = self._raw.get(key)
        if v is None:
            raise _NotMeasured(f"comando '{key}' falhou: {self._errors.get(key, 'sem resposta do aparelho')}")
        return v

    def _meminfo(self) -> Dict[str, int]:
        d: Dict[str, int] = {}
        for m in re.finditer(r"^(\w[\w()]*):\s+(\d+)\s*kB", self._need("meminfo"), re.M):
            d[m.group(1)] = int(m.group(2))
        if "MemTotal" not in d:
            raise _NotMeasured("/proc/meminfo sem MemTotal")
        return d

    def _dmem(self) -> Dict[str, Any]:
        txt = self._need("dmeminfo")
        out: Dict[str, Any] = {"procs": []}
        sec = re.search(r"Total PSS by process:\n(.*?)\n\n", txt, re.S)
        if sec:
            for m in re.finditer(r"^\s*([\d,]+)K: (\S+) \(pid (\d+)", sec.group(1), re.M):
                out["procs"].append((_int(m.group(1)), m.group(2), int(m.group(3))))
        m = re.search(r"Total RAM: ([\d,]+)K \(status (\w+)\)", txt)
        if m:
            out["status"] = m.group(2)
        for label, key in (("Free RAM", "free"), ("Used RAM", "used"), ("Lost RAM", "lost")):
            mm = re.search(rf"{label}: ([\d,]+)K", txt)
            if mm:
                out[key] = _int(mm.group(1))
        mz = re.search(r"ZRAM: ([\d,]+)K physical used for ([\d,]+)K in swap", txt)
        if mz:
            out["zram_phys"], out["zram_swap"] = _int(mz.group(1)), _int(mz.group(2))
        return out

    def _cpuinfo(self) -> Dict[str, Any]:
        txt = self._need("cpuinfo")
        out: Dict[str, Any] = {"procs": []}
        m = re.search(r"([\d.]+)% TOTAL: ([\d.]+)% user \+ ([\d.]+)% kernel(?: \+ ([\d.]+)% iowait)?", txt)
        if m:
            out["total"], out["user"], out["kernel"] = float(m.group(1)), float(m.group(2)), float(m.group(3))
            out["iowait"] = float(m.group(4) or 0)
        for m in re.finditer(r"^\s*([\d.]+)% (\d+)/([^:]+):", txt, re.M):
            out["procs"].append((float(m.group(1)), m.group(3).strip(), int(m.group(2))))
        if "total" not in out:
            raise _NotMeasured("dumpsys cpuinfo sem linha TOTAL")
        return out

    def _user_pkgs(self) -> set:
        return {l.split(":", 1)[1].strip() for l in self._need("pkgs_user").splitlines() if l.startswith("package:")}

    def _now(self) -> datetime:
        try:
            return datetime.strptime((self._raw.get("date") or "").strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.now()

    def _events(self) -> Dict[str, Any]:
        if "events_parsed" in self._facts:
            return self._facts["events_parsed"]
        txt = self._need("events")
        year = self._now().year
        stamps: List[datetime] = []
        kills: List[str] = []
        anrs = 0
        wake_on: List[int] = []
        wake_off: List[int] = []
        for line in txt.splitlines():
            m = re.match(r"(\d\d-\d\d \d\d:\d\d:\d\d)", line)
            if m:
                try:
                    stamps.append(datetime.strptime(f"{year}-{m.group(1)}", "%Y-%m-%d %H:%M:%S"))
                except ValueError:
                    pass
            if "am_kill" in line:
                mk = re.search(r"\[\d+,\d+,([^,]+),(-?\d+),(.*)\]", line)
                kills.append(re.sub(r"\s*#\d+", "", mk.group(3)).strip() if mk else "desconhecido")
            elif "am_anr" in line:
                anrs += 1
            elif "power_screen_broadcast_done" in line:
                mw = re.search(r"\[(\d),(\d+),", line)
                if mw:
                    (wake_on if mw.group(1) == "1" else wake_off).append(int(mw.group(2)))
        span_min = ((max(stamps) - min(stamps)).total_seconds() / 60.0) if len(stamps) > 1 else 0.0
        res = {"kills": kills, "anrs": anrs, "wake_on": wake_on, "wake_off": wake_off, "span_min": span_min}
        self._facts["events_parsed"] = res
        return res

    def _dropbox(self) -> Dict[str, List[datetime]]:
        txt = self._need("dropbox")
        d: Dict[str, List[datetime]] = {}
        for m in re.finditer(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\S+) \(", txt, re.M):
            try:
                d.setdefault(m.group(2), []).append(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                pass
        return d

    # ------------------------------------------------------------ execução
    def run_test(self, serial: str, test_id: str) -> TestResult:
        t0 = time.time()
        meta = next((t for t in self._tests_metadata if t["id"] == test_id), None)
        if not meta:
            return TestResult(test_id, test_id, "unknown", TestStatus.SKIPPED, "Teste inexistente.")
        if serial != self._serial or not self._raw:
            self.collect(serial)
        fn = getattr(self, f"_t_{test_id}", None)
        try:
            if fn is None:
                raise _NotMeasured("teste não implementado")
            status, msg, details = fn()
        except _NotMeasured as nm:
            status, msg, details = TestStatus.SKIPPED, f"Não medido: {nm}", {"Motivo": str(nm)}
        except Exception as exc:  # nunca aprovar em caso de erro
            logger.error(f"Erro no teste {test_id}: {exc}", exc_info=True)
            status, msg, details = TestStatus.SKIPPED, f"Não medido: erro ao analisar dados ({exc})", {"Erro": str(exc)}
        return TestResult(test_id, meta["name"], meta["category"], status, msg, details, int((time.time() - t0) * 1000))

    # ----------------------------------------------------------------- testes
    # Memória -----------------------------------------------------------------
    def _t_mem_total(self):
        m = self._meminfo()
        self._facts["ram_total_kb"] = m["MemTotal"]
        gb = m["MemTotal"] / 1024 / 1024
        note = "Pouca RAM para o Android atual: o aparelho sofre com muitos apps abertos." if gb < 3.0 else (
            "Capacidade de entrada/intermediária: sensível a excesso de apps em segundo plano." if gb < 4.5 else "RAM confortável.")
        return TestStatus.INFO, f"{_mb(m['MemTotal'])} instalados — {note}", {"RAM total": _mb(m["MemTotal"]), "Interpretação": note}

    def _t_mem_avail(self):
        m = self._meminfo()
        av, tot = m.get("MemAvailable", 0), m["MemTotal"]
        pct = av * 100 / tot
        self._facts.update(avail_kb=av, avail_pct=pct, memfree_kb=m.get("MemFree", 0))
        st = TestStatus.PASSED if pct >= 25 else TestStatus.WARNING if pct >= 12 else TestStatus.FAILED
        if av < 300 * 1024:
            st = TestStatus.FAILED
        verdict = {"passed": "adequada", "warning": "baixa", "failed": "crítica"}[st.value]
        return st, f"{_mb(av)} disponíveis de {_mb(tot)} ({pct:.0f}%) — {verdict}", {
            "Critério": "Aprovado ≥ 25% disponível; Atenção 12–25%; Falha < 12% ou < 300 MB",
            "Disponível": f"{_mb(av)} ({pct:.1f}%)", "Livre bruto": _mb(m.get('MemFree', 0)),
            "Cache": _mb(m.get('Cached', 0)),
            "Nota": "MemFree baixo é normal no Android; o que importa é MemAvailable."}

    def _t_mem_swap(self):
        m = self._meminfo()
        tot, free = m.get("SwapTotal", 0), m.get("SwapFree", 0)
        if tot <= 0:
            return TestStatus.INFO, "Sem swap/zRAM configurado", {}
        used = tot - free
        pct = used * 100 / tot
        self._facts.update(swap_used_kb=used, swap_total_kb=tot, swap_pct=pct)
        st = TestStatus.PASSED if pct < 30 else TestStatus.WARNING if pct < 60 else TestStatus.FAILED
        return st, f"{_mb(used)} de {_mb(tot)} em uso ({pct:.0f}%)" + (
            " — o sistema está usando swap pesadamente (RAM esgotada)" if st != TestStatus.PASSED else ""), {
            "Critério": "Aprovado < 30% do swap; Atenção 30–60%; Falha ≥ 60%",
            "Swap usado": _mb(used), "Swap total": _mb(tot),
            "Por que importa": "Swap alto = RAM insuficiente; o kernel gasta CPU comprimindo/descomprimindo páginas e o aparelho engasga."}

    def _t_mem_state(self):
        d = self._dmem()
        status = d.get("status")
        if not status:
            raise _NotMeasured("dumpsys meminfo não informou o estado de memória")
        self._facts["mem_state"] = status
        self._facts["lost_kb"] = d.get("lost", 0)
        st = {"normal": TestStatus.PASSED, "moderate": TestStatus.WARNING}.get(status, TestStatus.FAILED)
        zr = f" • zRAM: {_mb(d['zram_phys'])} físicos guardando {_mb(d['zram_swap'])}" if "zram_phys" in d else ""
        return st, f"Android reporta memória '{status}'{zr}", {
            "Critério": "Aprovado = normal; Atenção = moderate; Falha = low/critical",
            "Estado": status, "RAM usada": _mb(d.get("used", 0)), "RAM livre+cache": _mb(d.get("free", 0)),
            "RAM perdida (kernel/GPU)": _mb(d.get("lost", 0))}

    def _t_mem_bgproc(self):
        m = re.search(r"(\d+) total", self._need("lru"))
        if not m:
            raise _NotMeasured("lista LRU de processos indisponível")
        n = int(m.group(1))
        self._facts["lru"] = n
        st = TestStatus.PASSED if n <= 90 else TestStatus.WARNING if n <= 130 else TestStatus.FAILED
        return st, f"{n} processos mantidos na memória" + (" — acima do ideal para este aparelho" if st != TestStatus.PASSED else ""), {
            "Critério": "Aprovado ≤ 90; Atenção 91–130; Falha > 130 (heurística para aparelhos de ~4 GB)",
            "Processos": n}

    def _t_mem_lmk(self):
        ev = self._events()
        k = ev["kills"]
        span = ev["span_min"]
        if span < 5:
            raise _NotMeasured("janela do log de eventos muito curta para estimar taxa")
        per_h = len(k) * 60 / span
        self._facts.update(kills=len(k), kill_rate=per_h, kill_span=span)
        reasons = Counter(k).most_common(4)
        st = TestStatus.PASSED if per_h <= 30 else TestStatus.WARNING if per_h <= 100 else TestStatus.FAILED
        rs = ", ".join(f"{r} ×{c}" for r, c in reasons) or "nenhum"
        return st, f"{len(k)} apps encerrados em {span / 60:.1f} h (≈{per_h:.0f}/h) — motivos: {rs}", {
            "Critério": "Aprovado ≤ 30/h; Atenção 31–100/h; Falha > 100/h",
            "Encerramentos": len(k), "Janela": f"{span / 60:.1f} h", "Motivos": rs,
            "Nota": "'LockScreenClean' = a MIUI mata apps ao bloquear a tela; 'empty/cached' = falta de RAM."}

    # CPU ---------------------------------------------------------------------
    def _t_cpu_load(self):
        c = self._cpuinfo()
        self._facts["cpu_total"] = c["total"]
        st = TestStatus.PASSED if c["total"] < 50 else TestStatus.WARNING if c["total"] < 75 else TestStatus.FAILED
        if c["iowait"] >= 8 and st == TestStatus.PASSED:
            st = TestStatus.WARNING
        return st, f"{c['total']:.0f}% total ({c['user']:.0f}% usuário + {c['kernel']:.0f}% kernel + {c['iowait']:.1f}% espera de disco)", {
            "Critério": "Aprovado < 50%; Atenção 50–75% (ou iowait ≥ 8%); Falha ≥ 75%",
            "Janela": "últimos ~minutos (dumpsys cpuinfo)", "Total": f"{c['total']}%"}

    def _freqs(self) -> List[Tuple[int, int, int, int, str]]:
        rows = []
        for l in self._need("cpufreq").splitlines():
            p = l.split()
            if len(p) >= 5 and p[0].startswith("cpu"):
                rows.append((int(p[0][3:]), _int(p[1]), _int(p[2]), _int(p[3]), p[4]))
        if not rows:
            raise _NotMeasured("frequências da CPU inacessíveis neste aparelho")
        return rows

    def _t_cpu_throttle(self):
        rows = self._freqs()
        ratios = [(i, mx / hw) for i, cur, mx, hw, g in rows if hw > 0]
        worst = min(r for _, r in ratios)
        groups: Dict[int, List[int]] = {}
        for i, cur, mx, hw, g in rows:
            groups.setdefault(hw, []).append(mx)
        desc = " | ".join(f"hardware {hw / 1e6:.2f} GHz → limitado a {max(v) / 1e6:.2f} GHz ({max(v) * 100 / hw:.0f}%)" for hw, v in sorted(groups.items()))
        self._facts.update(cpu_worst_ratio=worst, cpu_cap_desc=desc)
        st = TestStatus.PASSED if worst >= 0.95 else TestStatus.WARNING if worst >= 0.75 else TestStatus.FAILED
        return st, desc, {
            "Critério": "Aprovado ≥ 95% do máximo de hardware; Atenção 75–95%; Falha < 75%",
            "Pior núcleo": f"{worst * 100:.0f}% do máximo",
            "Significado": "Frequência máxima permitida pelo sistema abaixo da capacidade do chip (limite térmico, de bateria ou de perfil de energia)."}

    def _t_cpu_cores(self):
        on = self._need("cpuonline").split("\n")
        if len(on) < 2:
            raise _NotMeasured("lista de núcleos indisponível")

        def count(s: str) -> int:
            n = 0
            for part in s.strip().split(","):
                if "-" in part:
                    a, b = part.split("-")
                    n += int(b) - int(a) + 1
                elif part.strip().isdigit():
                    n += 1
            return n
        n_on, n_all = count(on[0]), count(on[1])
        st = TestStatus.PASSED if n_on >= n_all else TestStatus.WARNING
        return st, f"{n_on} de {n_all} núcleos online", {"Critério": "Aprovado = todos os núcleos online", "Online": on[0], "Possíveis": on[1]}

    def _t_cpu_gov(self):
        gov = Counter(r[4] for r in self._freqs())
        return TestStatus.INFO, ", ".join(f"{g} ×{c}" for g, c in gov.items()), {"Governadores": dict(gov)}

    # Armazenamento ---------------------------------------------------------------
    def _t_sto_free(self):
        m = re.search(r"Data-Free: (\d+)K / (\d+)K total = (\d+)% free", self._need("diskstats"))
        if not m:
            raise _NotMeasured("diskstats sem Data-Free")
        free, tot, pct = int(m.group(1)), int(m.group(2)), int(m.group(3))
        self._facts.update(data_free_kb=free, data_total_kb=tot, data_free_pct=pct)
        st = TestStatus.PASSED if pct >= 15 else TestStatus.WARNING if pct >= 8 else TestStatus.FAILED
        return st, f"{_mb(free)} livres de {_mb(tot)} ({pct}%) — espaço {'suficiente' if st == TestStatus.PASSED else 'baixo'}", {
            "Critério": "Aprovado ≥ 15% livre; Atenção 8–15%; Falha < 8%"}

    def _t_sto_write(self):
        out = self._need("iotest")
        m = re.search(r"copied, ([\d.]+) s", out)
        if not m:
            raise _NotMeasured(f"teste de escrita não retornou tempo ({out.strip()[:80] or 'sem saída'})")
        secs = float(m.group(1))
        mbps = 64 / secs if secs > 0 else 0
        self._facts["io_mbps"] = mbps
        st = TestStatus.PASSED if mbps >= 40 else TestStatus.WARNING if mbps >= 15 else TestStatus.FAILED
        return st, f"{mbps:.0f} MB/s (64 MB em {secs:.2f} s) — memória interna {'saudável' if st == TestStatus.PASSED else 'lenta'}", {
            "Critério": "Aprovado ≥ 40 MB/s; Atenção 15–40; Falha < 15 (escrita sequencial com fsync)",
            "Velocidade": f"{mbps:.1f} MB/s", "Tempo": f"{secs:.3f} s"}

    def _t_sto_latency(self):
        m = re.search(r"Latency: (\d+)ms", self._need("diskstats"))
        if not m:
            raise _NotMeasured("diskstats sem latência")
        ms = int(m.group(1))
        self._facts["io_latency_ms"] = ms
        st = TestStatus.PASSED if ms <= 100 else TestStatus.WARNING if ms <= 500 else TestStatus.FAILED
        return st, f"{ms} ms para escrita de 512 B", {"Critério": "Aprovado ≤ 100 ms; Atenção ≤ 500 ms; Falha > 500 ms"}

    def _t_sto_mount(self):
        line = self._need("mounts").strip()
        if not line:
            raise _NotMeasured("/data não encontrado em /proc/mounts")
        rw = re.search(r"\brw\b", line) is not None
        return (TestStatus.PASSED if rw else TestStatus.FAILED), (
            "/data montado em leitura e escrita" if rw else "/data montado SOMENTE LEITURA — indica corrupção/falha da memória"), {
            "Critério": "Aprovado = rw", "Linha": line[:120]}

    def _t_sto_break(self):
        txt = self._need("diskstats")
        parts = []
        for label, key in (("Apps", "App Size"), ("Fotos", "Photos Size"), ("Vídeos", "Videos Size"),
                           ("Áudio", "Audio Size"), ("Sistema", "System Size"), ("Outros", "Other Size")):
            m = re.search(rf"^{key}: (\d+)", txt, re.M)
            if m:
                parts.append(f"{label} {int(m.group(1)) / 1024 ** 3:.1f} GB")
        if not parts:
            raise _NotMeasured("diskstats sem tamanhos")
        return TestStatus.INFO, " • ".join(parts), {"Detalhe": parts}

    # Bateria ---------------------------------------------------------------------
    def _batt(self) -> Dict[str, str]:
        d = {}
        for m in re.finditer(r"^\s*([A-Za-z ]+): (.+)$", self._need("battery"), re.M):
            d[m.group(1).strip().lower()] = m.group(2).strip()
        if "level" not in d:
            raise _NotMeasured("dumpsys battery sem nível")
        return d

    def _t_batt_level(self):
        b = self._batt()
        lvl = int(b["level"])
        self._facts["batt_level"] = lvl
        return (TestStatus.WARNING if lvl < 15 else TestStatus.INFO), f"{lvl}%" + (" — nível muito baixo" if lvl < 15 else ""), {"Nível": f"{lvl}%"}

    def _t_batt_health(self):
        b = self._batt()
        code = b.get("health", "")
        names = {"2": "Boa", "3": "Superaquecida", "4": "Morta", "5": "Sobretensão", "6": "Falha", "7": "Fria", "1": "Desconhecida"}
        st = TestStatus.PASSED if code == "2" else TestStatus.INFO if code in ("1", "") else TestStatus.FAILED
        return st, f"Android reporta: {names.get(code, code)} (código {code})", {
            "Critério": "Aprovado = código 2 (Boa)",
            "Aviso": "Este código só detecta falhas graves; NÃO mede desgaste. Veja 'Capacidade real estimada'."}

    def _t_batt_temp(self):
        t = int(self._batt()["temperature"]) / 10
        self._facts["batt_temp"] = t
        st = TestStatus.PASSED if t < 40 else TestStatus.WARNING if t < 45 else TestStatus.FAILED
        return st, f"{t:.1f} °C", {"Critério": "Aprovado < 40 °C; Atenção 40–45; Falha ≥ 45"}

    def _t_batt_volt(self):
        b = self._batt()
        v, lvl = int(b["voltage"]), int(b["level"])
        self._facts["batt_v"] = v
        st = TestStatus.PASSED
        note = "coerente com o nível de carga"
        if lvl >= 40 and v < 3600:
            st, note = TestStatus.FAILED, "tensão muito baixa para este nível — célula fraca"
        elif lvl >= 40 and v < 3750:
            st, note = TestStatus.WARNING, "tensão baixa para este nível"
        return st, f"{v} mV a {lvl}% — {note}", {
            "Critério": "Falha se < 3,60 V com ≥ 40% de carga; Atenção < 3,75 V",
            "Tensão": f"{v / 1000:.3f} V"}

    def _t_batt_capacity(self):
        b = self._batt()
        lvl = int(b["level"])
        txt = self._raw.get("bstats") or ""
        est = re.search(r"Estimated battery capacity: (\d+) mAh", txt)
        design = re.search(r"Capacity: (\d+), Computed drain", txt)
        design_mah = int(design.group(1)) if design else 0
        est_mah = int(est.group(1)) if est else 0
        counter = int(b.get("charge counter", "0") or 0)
        counter_mah = (counter / 1000 / lvl * 100) if lvl >= 15 and counter > 0 else 0
        if not design_mah or not (est_mah or counter_mah):
            raise _NotMeasured("Android não expôs capacidade de projeto/estimada (sem root não há charge_full)")
        pcts = [m * 100 / design_mah for m in (est_mah, counter_mah) if m]
        pct = sum(pcts) / len(pcts)
        self._facts.update(batt_cap_pct=pct, batt_design=design_mah, batt_est=est_mah, batt_counter_mah=counter_mah)
        st = TestStatus.PASSED if pct >= 85 else TestStatus.WARNING if pct >= 70 else TestStatus.FAILED
        return st, f"≈{pct:.0f}% da capacidade original ({est_mah or counter_mah:.0f} de {design_mah} mAh)" + (
            " — bateria desgastada" if st != TestStatus.PASSED else ""), {
            "Critério": "Aprovado ≥ 85%; Atenção 70–85%; Falha < 70% (estimativa)",
            "Estimativa Android": f"{est_mah} mAh", "Estimativa pelo contador de carga": f"{counter_mah:.0f} mAh",
            "Projeto": f"{design_mah} mAh",
            "Aviso": "Valores estimados: sem root o Android 10 não expõe charge_full nem ciclos."}

    def _t_batt_drain(self):
        m = re.search(r"Computed drain: ([\d.]+), actual drain: ([\d.]+)(?:-([\d.]+))?", self._raw.get("bstats") or "")
        if not m:
            raise _NotMeasured("batterystats sem consumo real/contabilizado")
        comp = float(m.group(1))
        act = (float(m.group(2)) + float(m.group(3) or m.group(2))) / 2
        if comp <= 0:
            raise _NotMeasured("consumo contabilizado = 0")
        ratio = act / comp
        self._facts["drain_ratio"] = ratio
        st = TestStatus.PASSED if ratio < 1.3 else TestStatus.WARNING if ratio < 2.0 else TestStatus.FAILED
        return st, f"descarga real {act:.0f} mAh vs {comp:.0f} mAh explicados pelos apps (×{ratio:.1f})", {
            "Critério": "Aprovado < ×1,3; Atenção ×1,3–2,0; Falha ≥ ×2,0",
            "Significado": "Razão alta = consumo não explicado por apps (hardware, bateria degradada ou estimativa imprecisa)."}

    def _t_batt_charge(self):
        b = self._batt()
        src = "USB" if b.get("usb powered") == "true" else "AC" if b.get("ac powered") == "true" else "sem fonte (na bateria)"
        cur = int(b.get("max charging current", "0") or 0) / 1000
        return TestStatus.INFO, f"{src}" + (f" — corrente máx. {cur:.0f} mA" if cur else ""), {"Fonte": src}

    # Térmico -------------------------------------------------------------------
    def _zones(self) -> Dict[str, float]:
        z: Dict[str, float] = {}
        for l in self._need("thermal").splitlines():
            p = l.split()
            if len(p) == 2 and re.match(r"-?\d+$", p[1]):
                v = int(p[1]) / 1000.0
                if 0 < v < 150 and not any(x in p[0] for x in ("lvl", "bcl", "soc")):
                    z[p[0]] = v
        if not z:
            raise _NotMeasured("zonas térmicas inacessíveis")
        return z

    def _t_therm_cpu(self):
        z = {k: v for k, v in self._zones().items() if k.startswith("cpu")}
        if not z:
            raise _NotMeasured("nenhuma zona térmica de CPU")
        k, mx = max(z.items(), key=lambda kv: kv[1])
        self._facts["cpu_temp"] = mx
        st = TestStatus.PASSED if mx < 55 else TestStatus.WARNING if mx < 70 else TestStatus.FAILED
        return st, f"máx. {mx:.1f} °C ({k}) em {len(z)} sensores", {"Critério": "Aprovado < 55 °C; Atenção 55–70; Falha ≥ 70", **{a: f"{b:.1f} °C" for a, b in z.items()}}

    def _t_therm_board(self):
        z = {k: v for k, v in self._zones().items() if k in ("xo-therm-adc", "quiet-therm-adc", "pm6125-tz", "pmi632-tz", "rf-pa0-therm-adc", "conn-therm-adc", "camera-ftherm-adc", "backlight_therm")}
        if not z:
            raise _NotMeasured("sensores de placa não encontrados")
        k, mx = max(z.items(), key=lambda kv: kv[1])
        st = TestStatus.PASSED if mx < 45 else TestStatus.WARNING if mx < 60 else TestStatus.FAILED
        return st, f"máx. {mx:.1f} °C ({k})", {"Critério": "Aprovado < 45 °C; Atenção 45–60; Falha ≥ 60", **{a: f"{b:.1f} °C" for a, b in z.items()}}

    def _t_therm_storage(self):
        z = self._zones()
        k = next((n for n in z if "emmc" in n or "ufs" in n), None)
        if not k:
            raise _NotMeasured("sensor de memória interna ausente")
        st = TestStatus.PASSED if z[k] < 55 else TestStatus.WARNING if z[k] < 70 else TestStatus.FAILED
        return st, f"{z[k]:.1f} °C", {"Critério": "Aprovado < 55 °C; Atenção 55–70; Falha ≥ 70"}

    # Display ---------------------------------------------------------------------
    def _t_disp_wake(self):
        ev = self._events()
        on, off = ev["wake_on"], ev["wake_off"]
        allv = on + off
        if not allv:
            raise _NotMeasured("sem eventos de tela no log recente (apague e acenda a tela e rode de novo)")
        worst = max(allv)
        self._facts.update(wake_on=on, wake_off=off, wake_worst=worst)
        st = TestStatus.PASSED if worst <= 1000 else TestStatus.WARNING if worst <= 2000 else TestStatus.FAILED
        return st, f"ligar: {', '.join(f'{x} ms' for x in on) or '—'} | apagar: {', '.join(f'{x} ms' for x in off) or '—'}" + (
            " — demora anormal" if st != TestStatus.PASSED else ""), {
            "Critério": "Aprovado ≤ 1000 ms; Atenção ≤ 2000 ms; Falha > 2000 ms",
            "O que é": "Tempo que o system_server leva para concluir a transição de tela (notificar todos os apps)."}

    def _t_disp_info(self):
        m = self._need("misc")
        size = re.search(r"Physical size: (\S+)", m)
        dens = re.search(r"Physical density: (\d+)", m)
        if not size:
            raise _NotMeasured("wm size indisponível")
        return TestStatus.INFO, f"{size.group(1)} @ {dens.group(1) if dens else '?'} dpi", {}

    # Sensores --------------------------------------------------------------------
    def _t_sen_core(self):
        m = self._need("misc")
        sens = m.split("===SENS", 1)[-1].split("===WM", 1)[0]
        need = {"Acelerômetro": "android.sensor.accelerometer", "Giroscópio": "android.sensor.gyroscope",
                "Proximidade": "android.sensor.proximity", "Luminosidade": "android.sensor.light",
                "Bússola": "android.sensor.magnetic_field("}
        have = {k: (v in sens) for k, v in need.items()}
        if not sens.strip():
            raise _NotMeasured("sensorservice sem lista de sensores")
        missing = [k for k, ok in have.items() if not ok]
        crit = [k for k in missing if k in ("Acelerômetro", "Proximidade")]
        st = TestStatus.FAILED if crit else TestStatus.WARNING if missing else TestStatus.PASSED
        return st, ("Todos presentes" if not missing else f"Ausentes: {', '.join(missing)}") + " (presença no sistema; não mede precisão)", {
            "Critério": "Aprovado = todos listados no sensorservice", **{k: "presente" if v else "AUSENTE" for k, v in have.items()}}

    # Rede ------------------------------------------------------------------------
    def _t_net_wifi(self):
        w = (self._need("misc").split("===SENS", 1)[0]).strip()
        if "SSID" not in w:
            raise _NotMeasured("Wi-Fi sem informação (desconectado ou desligado)")
        rssi = re.search(r"RSSI: (-?\d+)", w)
        spd = re.search(r"Link speed: (\d+)Mbps", w)
        ssid = re.search(r"SSID: ([^,]+)", w)
        r = int(rssi.group(1)) if rssi else -100
        st = TestStatus.PASSED if r >= -67 else TestStatus.WARNING if r >= -80 else TestStatus.FAILED
        return st, f"{ssid.group(1) if ssid else '?'}: {r} dBm, link {spd.group(1) if spd else '?'} Mbps", {
            "Critério": "Aprovado ≥ -67 dBm; Atenção -67 a -80; Falha < -80"}

    # Sistema ---------------------------------------------------------------------
    def _t_sys_version(self):
        p = self._facts.get("props", {})
        a, sdk = p.get("ro.build.version.release"), p.get("ro.build.version.sdk")
        if not a:
            raise _NotMeasured("propriedades indisponíveis")
        miui = p.get("ro.miui.ui.version.name")
        build = p.get("ro.build.version.incremental", "")
        self._facts.update(android=a, miui=miui, build=build)
        return TestStatus.INFO, f"Android {a} (API {sdk})" + (f" • MIUI {miui} {build}" if miui else ""), {
            "Fingerprint": p.get("ro.build.fingerprint", "")}

    def _t_sys_patch(self):
        patch = self._facts.get("props", {}).get("ro.build.version.security_patch", "")
        try:
            d = datetime.strptime(patch, "%Y-%m-%d")
        except ValueError:
            raise _NotMeasured("patch de segurança não informado")
        months = (self._now().year - d.year) * 12 + self._now().month - d.month
        self._facts["patch_months"] = months
        st = TestStatus.PASSED if months <= 12 else TestStatus.WARNING
        return st, f"{patch} — {months} meses atrás" + (" (sistema desatualizado)" if st != TestStatus.PASSED else ""), {
            "Critério": "Aprovado ≤ 12 meses; Atenção > 12 meses",
            "Impacto": "Versões antigas mantêm bugs de memória/estabilidade já corrigidos em atualizações."}

    def _t_sys_uptime(self):
        up = (self._need("misc").split("===UP", 1)[-1]).split()
        if not up:
            raise _NotMeasured("uptime indisponível")
        days = float(up[0]) / 86400
        self._facts["uptime_days"] = days
        st = TestStatus.PASSED if days < 7 else TestStatus.WARNING if days < 30 else TestStatus.FAILED
        return st, f"{days:.1f} dias sem reiniciar", {"Critério": "Aprovado < 7 dias; Atenção 7–30; Falha ≥ 30"}

    def _t_sys_stability(self):
        d = self._dropbox()
        now = self._now()
        boots = d.get("SYSTEM_BOOT", [])
        wd = d.get("system_server_watchdog", [])
        crash = d.get("system_server_crash", []) + d.get("SYSTEM_RESTART", [])
        recent_boots = [b for b in boots if (now - b).days < 7]
        self._facts.update(boots7=len(recent_boots), watchdog=len(wd), sys_crash=len(crash))
        st = TestStatus.PASSED
        if wd or crash:
            st = TestStatus.FAILED
        elif len(recent_boots) >= 3:
            st = TestStatus.WARNING
        return st, f"{len(recent_boots)} boots em 7 dias • {len(wd)} watchdog • {len(crash)} quedas do system_server", {
            "Critério": "Falha se houve watchdog/queda do system_server; Atenção ≥ 3 boots em 7 dias",
            "Nota": "O DropBox guarda poucos dias; ausência de registro não prova ausência de problema antigo."}

    def _settings(self) -> List[str]:
        p = self._need("settings").split()
        if len(p) < 3:
            raise _NotMeasured("settings indisponível")
        return p

    def _t_sys_anim(self):
        p = self._settings()[:3]
        vals = [_float(x, 1.0) for x in p]
        st = TestStatus.PASSED if max(vals) <= 1.0 else TestStatus.WARNING
        return st, f"janela {p[0]}x • transição {p[1]}x • animador {p[2]}x", {"Critério": "Aprovado ≤ 1,0x"}

    def _t_sys_saver(self):
        p = self._settings()
        on = len(p) > 3 and p[3] == "1"
        self._facts["saver_on"] = on
        return (TestStatus.WARNING if on else TestStatus.PASSED), (
            "Economia de energia ATIVA — limita CPU e segundo plano" if on else "Economia de energia desligada"), {
            "Critério": "Aprovado = desligada"}

    def _t_sys_boot(self):
        p = self._facts.get("props", {})
        vb, lock = p.get("ro.boot.verifiedbootstate"), p.get("ro.boot.flash.locked")
        if vb is None and lock is None:
            raise _NotMeasured("propriedades de boot indisponíveis")
        return TestStatus.INFO, f"Verified boot: {vb or '?'} • bootloader {'bloqueado' if lock == '1' else 'desbloqueado' if lock == '0' else '?'}", {}

    # Apps ------------------------------------------------------------------------
    def _t_app_user(self):
        n = len(self._user_pkgs())
        self._facts["user_apps"] = n
        st = TestStatus.PASSED if n <= 60 else TestStatus.WARNING if n <= 90 else TestStatus.FAILED
        return st, f"{n} apps de terceiros", {"Critério": "Aprovado ≤ 60; Atenção 61–90; Falha > 90 (heurística para ~4 GB de RAM)"}

    def _t_app_heavy(self):
        up = self._user_pkgs()
        procs = [(kb, n) for kb, n, _ in self._dmem()["procs"] if n.split(":")[0] in up]
        if not procs:
            return TestStatus.INFO, "Nenhum app de terceiros entre os maiores consumidores", {}
        agg: Dict[str, int] = {}
        for kb, n in procs:
            agg[n.split(":")[0]] = agg.get(n.split(":")[0], 0) + kb
        top = sorted(agg.items(), key=lambda kv: -kv[1])[:5]
        self._facts["heavy_apps"] = top
        st = TestStatus.WARNING if top[0][1] > 200 * 1024 else TestStatus.PASSED
        return st, " • ".join(f"{n.split('.')[-1] if n.count('.') else n} {_mb(kb)}" for n, kb in top), {
            "Critério": "Atenção se algum app de terceiros > 200 MB agora", **{n: _mb(kb) for n, kb in top}}

    def _t_app_bloat(self):
        allp = {l.split(":", 1)[1].strip() for l in self._need("pkgs_all").splitlines() if l.startswith("package:")}
        pss = {n.split(":")[0]: kb for kb, n, _ in self._dmem()["procs"]}
        cpu = {n.split(":")[0]: c for c, n, _ in self._cpuinfo()["procs"]}
        found = [(p, d) for p, d in KNOWN_HEAVY.items() if p in allp]
        self._facts["bloat"] = [(p, d, pss.get(p, 0), cpu.get(p, 0.0)) for p, d in found]
        if not found:
            return TestStatus.PASSED, "Nenhum serviço residente pesado conhecido encontrado", {"Critério": "Aprovado = nenhum da lista de conhecidos"}
        active = [(p, pss.get(p, 0), cpu.get(p, 0.0)) for p, _ in found if pss.get(p) or cpu.get(p)]
        st = TestStatus.WARNING if active else TestStatus.INFO
        txt = " • ".join(f"{p.split('.')[-1]} ({_mb(m)}, {c:.0f}% CPU)" for p, m, c in active) or f"{len(found)} instalados, inativos agora"
        return st, txt, {"Critério": "Atenção se algum estiver ativo consumindo RAM/CPU", **{p: d for p, d in found}}

    # Processos -------------------------------------------------------------------
    def _t_proc_cpu(self):
        c = self._cpuinfo()
        top = [(p, n) for p, n, _ in c["procs"] if n.split(":")[0].split("/")[0] not in SYSTEM_PROCS][:5]
        if not top:
            return TestStatus.INFO, "Sem consumidores relevantes", {}
        self._facts["cpu_top"] = top
        mx = top[0][0]
        st = TestStatus.PASSED if mx < 20 else TestStatus.WARNING if mx < 40 else TestStatus.FAILED
        return st, " • ".join(f"{n.split(':')[0].split('.')[-1]} {p:.0f}%" for p, n in top[:4]), {
            "Critério": "Aprovado: nenhum > 20% | Atenção 20–40% | Falha ≥ 40% (janela recente)", **{n: f"{p}%" for p, n in top}}

    def _anr_proc_counts(self) -> Counter:
        txt = self._need("anr_procs")
        return Counter(m.group(1) for m in re.finditer(r"^Process: (\S+)", txt, re.M))

    def _t_proc_anr(self):
        d = self._dropbox()
        entries = d.get("data_app_anr", []) + d.get("system_app_anr", [])
        now = self._now()
        last24 = [e for e in entries if (now - e).total_seconds() < 86400]
        procs = self._anr_proc_counts() if self._raw.get("anr_procs") is not None else Counter()
        self._facts.update(anr_total=len(entries), anr_24h=len(last24), anr_procs=procs.most_common(6))
        st = TestStatus.PASSED if len(last24) == 0 else TestStatus.WARNING if len(last24) <= 5 else TestStatus.FAILED
        top = ", ".join(f"{p} ×{c}" for p, c in procs.most_common(4))
        return st, f"{len(last24)} nas últimas 24 h ({len(entries)} no histórico)" + (f" — mais frequentes: {top}" if top else ""), {
            "Critério": "Aprovado = 0 em 24 h; Atenção 1–5; Falha > 5",
            "O que é": "ANR = o app/serviço parou de responder por vários segundos (o 'travamento' que você percebe)."}

    def _t_proc_native(self):
        d = self._dropbox()
        t = d.get("SYSTEM_TOMBSTONE", []) + d.get("data_app_native_crash", [])
        txt = self._raw.get("tomb_procs") or ""
        procs = Counter(re.sub(r"[<> ]", "", m.group(1)) for m in re.finditer(r"^>>> (.+?) <<<", txt, re.M))
        procs.update(m.group(1) for m in re.finditer(r"^Process: (\S+)", txt, re.M))
        self._facts["tombs"] = (len(t), procs.most_common(4))
        st = TestStatus.PASSED if len(t) < 3 else TestStatus.WARNING if len(t) < 10 else TestStatus.FAILED
        top = ", ".join(f"{p} ×{c}" for p, c in procs.most_common(3))
        return st, f"{len(t)} falhas nativas registradas" + (f" — {top}" if top else ""), {
            "Critério": "Aprovado < 3; Atenção 3–9; Falha ≥ 10"}

    # ---------------------------------------------------------------- análise
    def analyze(self, results: List[TestResult]) -> Tuple[List[Finding], str]:
        """Correlaciona os resultados e explica as causas prováveis, com evidências."""
        f = self._facts
        by = {r.test_id: r for r in results}

        def bad(*ids: str) -> bool:
            return any(i in by and by[i].status in (TestStatus.WARNING, TestStatus.FAILED) for i in ids)

        def crit(*ids: str) -> bool:
            return any(i in by and by[i].status == TestStatus.FAILED for i in ids)

        out: List[Finding] = []

        if bad("mem_avail", "mem_swap", "mem_state", "mem_bgproc"):
            ev = []
            if "avail_pct" in f:
                ev.append(f"RAM disponível {_mb(f['avail_kb'])} ({f['avail_pct']:.0f}% de {_mb(f['ram_total_kb'])})")
            if "swap_pct" in f:
                ev.append(f"swap {f['swap_pct']:.0f}% usado ({_mb(f['swap_used_kb'])})")
            if "lru" in f:
                ev.append(f"{f['lru']} processos na memória")
            if f.get("mem_state") and f["mem_state"] != "normal":
                ev.append(f"Android reporta memória '{f['mem_state']}'")
            out.append(Finding(
                "critical" if crit("mem_avail", "mem_swap", "mem_state", "mem_bgproc") else "warning",
                "Pressão de memória: a RAM está esgotada e o sistema vive em swap",
                "; ".join(ev) + ".",
                "Sem RAM livre o Android mata e recarrega apps o tempo todo e usa a CPU para comprimir memória. "
                "Resultado: lentidão geral, engasgos, apps que reabrem do zero e o system_server ocupado (que atrasa até acender a tela).",
                "Reduza o que fica residente: desinstale/desative apps que você não usa (lista abaixo), desligue o feed da home (App Vault) "
                "e os anúncios da MIUI, e evite 'limpadores de memória'. Se continuar com pouca RAM mesmo assim, o limite é do hardware.",
                ["mem_avail", "mem_swap", "mem_state", "mem_bgproc", "mem_lmk"]))

        if bad("proc_anr"):
            pr = f.get("anr_procs") or []
            out.append(Finding(
                "critical" if crit("proc_anr") else "warning",
                f"Apps parando de responder (ANR): {f.get('anr_24h', 0)} nas últimas 24 h",
                f"{f.get('anr_total', 0)} ANRs no histórico do sistema. Mais frequentes: " +
                (", ".join(f"{p} ×{c}" for p, c in pr) or "origem não identificada") + ".",
                "Cada ANR é um travamento real percebido por você (a tela congela até o app ou serviço voltar). "
                "ANR em processos de sistema (SystemUI/launcher/system) deixa o aparelho inteiro travado.",
                "Atualize ou desinstale os apps que mais aparecem; apps de sistema da MIUI na lista podem ser desativados. "
                "Reduzir a pressão de memória diminui muito os ANRs.",
                ["proc_anr"]))

        if bad("disp_wake"):
            out.append(Finding(
                "critical" if crit("disp_wake") else "warning",
                "Demora para ligar/apagar a tela confirmada em medição",
                f"Transições de tela medidas: ligar {f.get('wake_on')} ms, apagar {f.get('wake_off')} ms (normal ≤ 1000 ms).",
                "A tela só termina de acender quando o system_server conclui a notificação aos apps. Com RAM esgotada, "
                "apps travados (ANR) ou processos em swap, essa etapa leva segundos — exatamente o sintoma 'tela apaga e demora a ligar'.",
                "Resolver a pressão de memória e os ANRs acima. Se mesmo com RAM livre persistir, investigue bateria (queda de tensão) e atualização do sistema.",
                ["disp_wake"]))

        if bad("cpu_throttle"):
            temp = f.get("cpu_temp")
            reason = []
            if f.get("saver_on"):
                reason.append("a economia de energia está ligada (causa direta provável)")
            if temp is not None and temp < 55:
                reason.append(f"a temperatura é normal ({temp:.0f} °C), então não é superaquecimento")
            if bad("batt_capacity", "batt_volt"):
                reason.append("a bateria está desgastada — hipótese: o sistema limita o clock para evitar queda de tensão (não é medição direta; a MIUI também aplica limites por perfil de energia)")
            out.append(Finding(
                "warning",
                "CPU limitada abaixo da capacidade do chip",
                f"{f.get('cpu_cap_desc', '')}. " + ((reason[0][0].upper() + reason[0][1:] + ("; " + "; ".join(reason[1:]) if len(reason) > 1 else "") + ".") if reason else ""),
                "O processador está proibido de usar parte da sua velocidade máxima, o que soma à lentidão sob carga.",
                "Desative economia de energia / modo bateria agressivo em Segurança > Bateria e teste o modo de desempenho. "
                "Se o limite persistir com temperatura normal, pode estar ligado à bateria degradada ou ao perfil de energia da MIUI.",
                ["cpu_throttle", "therm_cpu", "sys_saver"]))

        if bad("batt_capacity", "batt_volt", "batt_drain"):
            pct = f.get("batt_cap_pct")
            out.append(Finding(
                "critical" if crit("batt_capacity", "batt_volt") else "warning",
                f"Bateria desgastada (~{pct:.0f}% da capacidade original)" if pct else "Bateria com sinais de desgaste",
                (f"Capacidade estimada {f.get('batt_est') or f.get('batt_counter_mah', 0):.0f} mAh de {f.get('batt_design')} mAh de projeto" if pct else "") +
                (f"; descarga real ×{f['drain_ratio']:.1f} maior que a explicada pelos apps" if "drain_ratio" in f else "") + ".",
                "Bateria fraca sofre queda de tensão quando a CPU pede energia: o sistema reduz o clock e, nos casos graves, apaga a tela ou desliga sem aviso. "
                "Também reduz a autonomia.",
                "Se houver desligamentos/apagões inesperados ou autonomia ruim, troque a bateria — é o que mais devolve estabilidade nesse perfil de desgaste. "
                "Valores são estimativas (Android 10 sem root não expõe os ciclos).",
                ["batt_capacity", "batt_volt", "batt_drain"]))

        heavy = f.get("heavy_apps") or []
        cputop = f.get("cpu_top") or []
        bloat = [b for b in f.get("bloat", []) if b[2] or b[3]]
        if bad("app_heavy", "app_bloat", "proc_cpu", "app_user"):
            lines = []
            for p, d, m, c in bloat:
                lines.append(f"{p} — {d} ({_mb(m)} RAM, {c:.0f}% CPU)")
            for n, kb in heavy[:3]:
                lines.append(f"{n} — app de terceiros usando {_mb(kb)} de RAM")
            for p, n in cputop[:2]:
                if p >= 20 and not any(n.startswith(b[0]) for b in bloat):
                    lines.append(f"{n} — {p:.0f}% de CPU na janela recente")
            out.append(Finding(
                "warning", "Candidatos concretos a aliviar o aparelho",
                " | ".join(lines) + f" | {f.get('user_apps', '?')} apps de terceiros instalados.",
                "São os processos que mais ocupam RAM/CPU agora e ficam residentes em segundo plano, alimentando a pressão de memória.",
                "Revise esta lista: desinstale o que não usa e desative os serviços MIUI/Facebook residentes (reversível). "
                "A ferramenta não remove nada sem sua ação.",
                ["app_heavy", "app_bloat", "proc_cpu", "app_user"]))

        if bad("sys_patch"):
            out.append(Finding(
                "warning", "Sistema desatualizado",
                f"Patch de segurança de {f.get('patch_months', '?')} meses atrás; Android {f.get('android', '?')}" + (f", MIUI {f.get('miui')} {f.get('build')}" if f.get('miui') else "") + ".",
                "Builds antigas mantêm problemas conhecidos de gerenciamento de memória e estabilidade que já foram corrigidos.",
                "Verifique se há atualização oficial em Configurações > Sobre o telefone. Se não houver, considere ROM atualizada.",
                ["sys_patch", "sys_version"]))

        if bad("sys_stability"):
            out.append(Finding(
                "critical", "Quedas/reinicializações do sistema registradas",
                by["sys_stability"].message,
                "Watchdog/queda do system_server significam que o Android inteiro travou ou reiniciou — compatível com os 'apagões' relatados.",
                "Priorize memória, bateria e atualização; exporte o relatório se for levar à assistência.",
                ["sys_stability"]))

        # O que foi DESCARTADO (também é resposta ao usuário)
        cleared = []
        if "data_free_pct" in f and not bad("sto_free"):
            cleared.append(f"espaço livre ({_mb(f['data_free_kb'])}, {f['data_free_pct']}%)")
        if "io_mbps" in f and not bad("sto_write", "sto_latency"):
            cleared.append(f"velocidade da memória interna ({f['io_mbps']:.0f} MB/s de escrita)")
        if "cpu_temp" in f and not bad("therm_cpu", "therm_board"):
            cleared.append(f"temperatura ({f['cpu_temp']:.0f} °C)")
        if cleared:
            out.append(Finding(
                "info", "Descartado como causa: " + ", ".join(cleared),
                "Medido com teste real de escrita e leitura de sensores.",
                "Ter espaço livre não evita lentidão: o gargalo aqui é RAM/swap e processos, não o armazenamento.",
                "Nenhuma ação necessária nesses itens.", ["sto_free", "sto_write", "sto_latency", "therm_cpu"]))

        order = {"critical": 0, "warning": 1, "info": 2}
        out.sort(key=lambda x: order[x.severity])
        causes = [x.title for x in out if x.severity != "info"][:3]
        skipped = [r.name for r in results if r.status == TestStatus.SKIPPED]
        summary = ("Causas prováveis: " + " • ".join(causes) + ".") if causes else \
            "Nenhuma anomalia relevante foi medida nos itens avaliados."
        if skipped:
            summary += f" ({len(skipped)} itens não puderam ser medidos neste aparelho.)"
        return out, summary

    # ------------------------------------------------------------ API em lote
    @staticmethod
    def score(results: List[TestResult]) -> int:
        m = [r for r in results if r.status in (TestStatus.PASSED, TestStatus.WARNING, TestStatus.FAILED)]
        if not m:
            return 0
        pts = sum(100 if r.status == TestStatus.PASSED else 50 if r.status == TestStatus.WARNING else 0 for r in m)
        return int(pts / len(m))

    def build_report(self, serial: str, start: datetime, results: List[TestResult]) -> DiagnosticReport:
        findings, summary = self.analyze(results)
        cnt = Counter(r.status for r in results)
        return DiagnosticReport(
            device_serial=serial, start_time=start, end_time=datetime.now(),
            overall_score=self.score(results),
            passed_count=cnt[TestStatus.PASSED], warning_count=cnt[TestStatus.WARNING],
            failed_count=cnt[TestStatus.FAILED], skipped_count=cnt[TestStatus.SKIPPED],
            info_count=cnt[TestStatus.INFO], results=results, findings=findings, summary=summary)

    def run_all_tests(self, serial: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> DiagnosticReport:
        start = datetime.now()
        self.collect(serial, (lambda i, n, label: progress_callback(int(i * 50 / n), label)) if progress_callback else None)
        results = []
        tests = self.get_available_tests()
        for i, t in enumerate(tests):
            if progress_callback:
                progress_callback(50 + int(i * 50 / len(tests)), f"Analisando: {t['name']}")
            results.append(self.run_test(serial, t["id"]))
        if progress_callback:
            progress_callback(100, "Diagnóstico completo.")
        return self.build_report(serial, start, results)


class _NotMeasured(Exception):
    """O dado necessário não pôde ser lido do aparelho (resulta em SKIPPED, nunca em aprovado)."""
