"""
Motor de Otimização e Limpeza do Sistema Android (Mobile-Diag-Pro).
Executa rotinas avançadas de alívio de CPU, limpeza de cache, liberação de memória RAM,
suspensão de processos pesados em segundo plano e restrição de bloatware via ADB.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from src.core.adb_commands import ADBCommands
from src.core.logger import get_logger

logger = get_logger(__name__)

# Aplicativos críticos de sistema que NUNCA devem ser interrompidos
SYSTEM_WHITELIST = {
    "android",
    "com.android.systemui",
    "com.android.settings",
    "com.android.phone",
    "com.android.launcher",
    "com.android.launcher3",
    "com.miui.home",
    "com.sec.android.app.launcher",
    "com.google.android.inputmethod.latin",
    "com.google.android.inputmethod.pinyin",
    "com.touchtype.swiftkey",
    "com.android.server.telecom",
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.android.vending",
}


class OptimizerEngine:
    """
    Controlador de otimização no estilo CCleaner / Advanced SystemCare para Android.
    """

    def __init__(self, adb_commands: Optional[ADBCommands] = None):
        self.adb = adb_commands or ADBCommands()

    def get_system_snapshot(self, serial: str) -> Dict[str, Any]:
        """
        Coleta dados de telemetria imediata (RAM, Swap, Processos ativos).
        """
        mem_info = self.adb.get_memory_info(serial)
        total_bytes = mem_info.get("memtotal", mem_info.get("total", 0))
        free_bytes = mem_info.get("memfree", mem_info.get("free", 0))
        avail_bytes = mem_info.get("memavailable", mem_info.get("available", 0))
        swap_total_bytes = mem_info.get("swaptotal", mem_info.get("swap_total", 0))
        swap_free_bytes = mem_info.get("swapfree", mem_info.get("swap_free", 0))

        total_mb = int(total_bytes // (1024 * 1024))
        avail_mb = int(avail_bytes // (1024 * 1024))
        free_mb = int(free_bytes // (1024 * 1024))
        swap_total_mb = int(swap_total_bytes // (1024 * 1024))
        swap_free_mb = int(swap_free_bytes // (1024 * 1024))

        running_apps = self.get_running_third_party_apps(serial)

        return {
            "mem_total_mb": total_mb,
            "mem_available_mb": avail_mb,
            "mem_free_mb": free_mb,
            "swap_total_mb": swap_total_mb,
            "swap_free_mb": swap_free_mb,
            "swap_used_mb": max(0, swap_total_mb - swap_free_mb),
            "running_third_party_count": len(running_apps),
            "running_apps": running_apps,
        }


    def get_running_third_party_apps(self, serial: str) -> List[Dict[str, Any]]:
        """
        Retorna a lista de aplicativos instalados pelo usuário que estão em execução.
        """
        try:
            # Obter lista de pacotes de terceiros
            raw_packages = self.adb.client.shell(serial, "pm list packages -3", timeout=8)
            installed_3rd = set()
            for line in raw_packages.splitlines():
                line = line.strip()
                if line.startswith("package:"):
                    pkg = line.replace("package:", "").strip()
                    if pkg and pkg not in SYSTEM_WHITELIST:
                        installed_3rd.add(pkg)

            # Obter processos em execução com consumo de RSS
            ps_output = self.adb.client.shell(serial, "ps -A -o NAME,PID,RSS", timeout=8)
            running_list = []
            seen_pkgs = set()

            for line in ps_output.splitlines():
                parts = line.strip().split()
                if len(parts) >= 3:
                    name = parts[0]
                    # Verificar se o processo pertence a algum pacote de terceiro
                    matched_pkg = None
                    for pkg in installed_3rd:
                        if name == pkg or name.startswith(pkg + ":"):
                            matched_pkg = pkg
                            break

                    if matched_pkg and matched_pkg not in seen_pkgs:
                        seen_pkgs.add(matched_pkg)
                        try:
                            rss_kb = int(parts[2])
                        except ValueError:
                            rss_kb = 0
                        running_list.append({
                            "package": matched_pkg,
                            "process_name": name,
                            "pid": parts[1],
                            "rss_mb": round(rss_kb / 1024, 1),
                        })

            running_list.sort(key=lambda x: x["rss_mb"], reverse=True)
            return running_list
        except Exception as e:
            logger.warning(f"Erro ao obter apps de terceiros em execução: {e}")
            return []

    def run_optimization(
        self,
        serial: str,
        options: Optional[Dict[str, bool]] = None,
        progress_cb: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executa a rotina completa de otimização no aparelho.
        
        Opções suportadas:
        - kill_background (bool): Encerrar processos ociosos (am kill-all)
        - stop_heavy_apps (bool): Forçar parada de apps pesados de terceiros em segundo plano
        - trim_caches (bool): Limpar caches de sistema e aplicativos
        - compact_ram (bool): Enviar trim-memory para o kernel e compactar ZRAM
        - clear_logs (bool): Limpar buffers do logcat e relatórios de falha (desafoga CPU)
        - speed_animations (bool): Aplicar escala de animação 0.5x para máxima responsividade
        """
        opts = options or {
            "kill_background": True,
            "stop_heavy_apps": True,
            "trim_caches": True,
            "compact_ram": True,
            "clear_logs": True,
            "speed_animations": False,
        }

        def report(pct: int, msg: str):
            if progress_cb:
                progress_cb(pct, msg)

        report(5, "Analisando estado da memória e processos ativos...")
        before_snap = self.get_system_snapshot(serial)
        time.sleep(0.3)

        stopped_apps = []
        logs_cleared = False
        cache_trimmed = False
        ram_compacted = False
        animations_applied = False

        # 1. Encerrar processos ociosos do sistema
        if opts.get("kill_background", True):
            report(20, "Encerrando tarefas ociosas em cache (am kill-all)...")
            try:
                self.adb.client.shell(serial, "am kill-all", timeout=10)
            except Exception as e:
                logger.warning(f"Erro em am kill-all: {e}")

        # 2. Suspender apps pesados de terceiros em segundo plano
        if opts.get("stop_heavy_apps", True):
            report(40, "Suspendendo aplicativos pesados de terceiros em segundo plano...")
            running_apps = before_snap.get("running_apps", [])
            for item in running_apps:
                pkg = item["package"]
                if pkg not in SYSTEM_WHITELIST:
                    try:
                        self.adb.client.shell(serial, f"am force-stop {pkg}", timeout=5)
                        stopped_apps.append(pkg)
                    except Exception as e:
                        logger.warning(f"Erro ao parar pacote {pkg}: {e}")

        # 3. Limpeza de Caches de Apps e Sistema
        if opts.get("trim_caches", True):
            report(60, "Limpando caches de armazenamento do sistema (pm trim-caches)...")
            try:
                self.adb.client.shell(serial, "pm trim-caches 99999999999", timeout=15)
                cache_trimmed = True
            except Exception as e:
                logger.warning(f"Erro em pm trim-caches: {e}")

        # 4. Limpar Buffers de Logcat e DropBox (alívio imediato do logd e CPU)
        if opts.get("clear_logs", True):
            report(75, "Limpando buffers de log do sistema e histórico de falhas...")
            try:
                self.adb.client.shell(serial, "logcat -c; dumpsys dropbox --empty", timeout=8)
                logs_cleared = True
            except Exception as e:
                logger.warning(f"Erro ao limpar logs: {e}")

        # 5. Compactação e Trim de Memória RAM & ZRAM
        if opts.get("compact_ram", True):
            report(85, "Compactando memória RAM e liberando blocos de swap...")
            try:
                # Disparar GC do sistema e trim
                self.adb.client.shell(serial, "am send-trim-memory", timeout=8)
                # Tentar compactar zram via sysfs se houver permissão
                self.adb.client.shell(serial, "echo 3 > /proc/sys/vm/drop_caches 2>/dev/null; echo 1 > /proc/sys/vm/compact_memory 2>/dev/null", timeout=5)
                ram_compacted = True
            except Exception as e:
                logger.warning(f"Erro em compact_ram: {e}")

        # 6. Modo Turbo de Animações
        if opts.get("speed_animations", False):
            report(92, "Acelerando velocidade de resposta de animações (0.5x)...")
            try:
                self.adb.client.shell(serial, "settings put global window_animation_scale 0.5; settings put global transition_animation_scale 0.5; settings put global animator_duration_scale 0.5", timeout=5)
                animations_applied = True
            except Exception as e:
                logger.warning(f"Erro ao acelerar animações: {e}")

        report(96, "Medindo ganhos de desempenho obtidos...")
        time.sleep(0.5)
        after_snap = self.get_system_snapshot(serial)

        # Cálculo de ganhos
        ram_freed_mb = max(0, after_snap["mem_available_mb"] - before_snap["mem_available_mb"])
        swap_freed_mb = max(0, after_snap["swap_free_mb"] - before_snap["swap_free_mb"])

        report(100, "Otimização concluída com sucesso!")

        return {
            "success": True,
            "before": before_snap,
            "after": after_snap,
            "ram_freed_mb": ram_freed_mb,
            "swap_freed_mb": swap_freed_mb,
            "stopped_apps_count": len(stopped_apps),
            "stopped_apps": stopped_apps,
            "cache_trimmed": cache_trimmed,
            "logs_cleared": logs_cleared,
            "ram_compacted": ram_compacted,
            "animations_applied": animations_applied,
        }

    def restrict_background_app(self, serial: str, package: str) -> bool:
        """
        Impede que um app de terceiro continue rodando ou iniciando em segundo plano via AppOps.
        """
        try:
            cmd = f"cmd appops set {package} RUN_IN_BACKGROUND ignore; cmd appops set {package} RUN_ANY_IN_BACKGROUND ignore"
            self.adb.client.shell(serial, cmd, timeout=5)
            return True
        except Exception as e:
            logger.error(f"Erro ao restringir app {package}: {e}")
            return False

    def unrestrict_background_app(self, serial: str, package: str) -> bool:
        """
        Restaura a permissão normal de execução em segundo plano para o app.
        """
        try:
            cmd = f"cmd appops set {package} RUN_IN_BACKGROUND allow; cmd appops set {package} RUN_ANY_IN_BACKGROUND allow"
            self.adb.client.shell(serial, cmd, timeout=5)
            return True
        except Exception as e:
            logger.error(f"Erro ao desrestringir app {package}: {e}")
            return False

    def uninstall_user_package(self, serial: str, package: str) -> bool:
        """
        Remove com segurança um app para o usuário 0 (desinstalação sem root).
        """
        try:
            out = self.adb.client.shell(serial, f"pm uninstall -k --user 0 {package}", timeout=10)
            return "Success" in out
        except Exception as e:
            logger.error(f"Erro ao desinstalar {package}: {e}")
            return False
