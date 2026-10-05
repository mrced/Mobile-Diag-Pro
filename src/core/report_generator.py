"""
Gerador de Relatórios Técnicos (HTML e JSON).
Exporta relatório de saúde e causa raiz formatado profissionalmente (estilo Apple Dark/Light).
"""
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any

from src.core.diagnostic_engine import DiagnosticReport, TestStatus


class ReportGenerator:
    """
    Gerador de relatórios visuais (HTML) e analíticos (JSON).
    Apresenta métricas reais, critérios de aprovação e análise de causas raiz.
    """

    def _get_css(self) -> str:
        return """
        :root {
            --bg-color: #1c1c1e;
            --surface-color: #2c2c2e;
            --surface-card: #252527;
            --text-primary: #f5f5f7;
            --text-secondary: #98989d;
            --accent-color: #0a84ff;
            --pass-color: #30d158;
            --warn-color: #ff9f0a;
            --fail-color: #ff453a;
            --info-color: #64b5ff;
            --border-color: rgba(255, 255, 255, 0.1);
        }
        @media (prefers-color-scheme: light) {
            :root {
                --bg-color: #f5f5f7;
                --surface-color: #ffffff;
                --surface-card: #f9f9fb;
                --text-primary: #1d1d1f;
                --text-secondary: #86868b;
                --accent-color: #007aff;
                --pass-color: #34c759;
                --warn-color: #ff9500;
                --fail-color: #ff3b30;
                --info-color: #007aff;
                --border-color: rgba(0, 0, 0, 0.1);
            }
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 24px;
            line-height: 1.5;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 24px;
        }
        .header h1 {
            margin: 0 0 6px 0;
            font-size: 24px;
        }
        .header p {
            margin: 0;
            color: var(--text-secondary);
            font-size: 13px;
        }
        .score-badge {
            display: inline-block;
            font-size: 2.4em;
            font-weight: 700;
            padding: 8px 28px;
            border-radius: 40px;
            background-color: var(--surface-color);
            border: 2px solid var(--accent-color);
            color: var(--accent-color);
            margin: 16px 0;
        }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }
        .card {
            background-color: var(--surface-color);
            border-radius: 10px;
            padding: 14px 10px;
            text-align: center;
            border: 1px solid var(--border-color);
        }
        .card h3 { margin: 0; font-size: 0.75em; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
        .card .value { font-size: 1.6em; font-weight: bold; margin-top: 6px; }
        .val-pass { color: var(--pass-color); }
        .val-warn { color: var(--warn-color); }
        .val-fail { color: var(--fail-color); }
        .val-info { color: var(--info-color); }
        .val-time { color: var(--text-primary); }

        .findings-box {
            background-color: var(--surface-color);
            border: 1px solid rgba(10, 132, 255, 0.4);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .findings-box h2 {
            margin: 0 0 14px 0;
            font-size: 18px;
            color: var(--accent-color);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .finding-item {
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 10px;
            border: 1px solid var(--border-color);
        }
        .finding-item.critical {
            background-color: rgba(255, 69, 58, 0.12);
            border-color: rgba(255, 69, 58, 0.4);
        }
        .finding-item.warning {
            background-color: rgba(255, 159, 10, 0.12);
            border-color: rgba(255, 159, 10, 0.4);
        }
        .finding-item.info {
            background-color: rgba(10, 132, 255, 0.10);
            border-color: rgba(10, 132, 255, 0.3);
        }
        .finding-title {
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 4px;
        }
        .finding-badge {
            display: inline-block;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
            margin-right: 6px;
            color: #fff;
        }
        .finding-badge.critical { background-color: var(--fail-color); }
        .finding-badge.warning { background-color: var(--warn-color); }
        .finding-badge.info { background-color: var(--accent-color); }
        .finding-field {
            font-size: 12px;
            margin-top: 4px;
        }

        .category {
            background-color: var(--surface-color);
            border-radius: 12px;
            margin-bottom: 16px;
            padding: 18px;
            border: 1px solid var(--border-color);
        }
        .category h2 {
            margin: 0 0 10px 0;
            font-size: 15px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }
        .test-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
        }
        .test-row:last-child {
            border-bottom: none;
        }
        .test-info h4 { margin: 0 0 3px 0; font-size: 13px; color: var(--text-primary); }
        .test-info p { margin: 0; font-size: 12px; color: var(--text-secondary); }
        .pill {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .pill.passed { background-color: rgba(48, 209, 88, 0.2); color: var(--pass-color); }
        .pill.warning { background-color: rgba(255, 159, 10, 0.2); color: var(--warn-color); }
        .pill.failed { background-color: rgba(255, 69, 58, 0.2); color: var(--fail-color); }
        .pill.info { background-color: rgba(100, 181, 255, 0.2); color: var(--info-color); }
        .pill.skipped { background-color: rgba(142, 142, 147, 0.2); color: var(--text-secondary); }

        @media print {
            body { background-color: white; color: black; }
            .card, .category, .findings-box { box-shadow: none; border: 1px solid #ccc; }
        }
        """

    def generate_html(
        self, 
        report: DiagnosticReport, 
        output_path: Union[Path, str], 
        device_info: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Gera relatório HTML visual completo com diagnóstico e causas raiz.
        """
        out_p = Path(output_path)
        if isinstance(device_info, (str, Path)) and not isinstance(output_path, (str, Path)):
            out_p, device_info = Path(device_info), None

        html = [
            "<!DOCTYPE html>",
            "<html lang='pt-BR'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Relatório Técnico de Diagnóstico - Mobile-Diag-Pro</title>",
            f"<style>{self._get_css()}</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            "<div class='header'>",
            "<h1>Relatório Técnico de Diagnóstico Android</h1>",
            f"<p>Dispositivo: {report.device_serial} • Conclusão em: {report.end_time.strftime('%d/%m/%Y às %H:%M:%S')}</p>"
        ]

        if device_info and isinstance(device_info, dict):
            brand = device_info.get("brand", "")
            model = device_info.get("model", "")
            html.append(f"<p><strong>Modelo:</strong> {brand} {model}</p>")

        html.extend([
            f"<div class='score-badge'>{report.overall_score}%</div>",
            "</div>",
            "<div class='summary-cards'>"
        ])

        html.append(f"<div class='card'><h3>Aprovados</h3><div class='value val-pass'>{report.passed_count}</div></div>")
        html.append(f"<div class='card'><h3>Atenção</h3><div class='value val-warn'>{report.warning_count}</div></div>")
        html.append(f"<div class='card'><h3>Falhas</h3><div class='value val-fail'>{report.failed_count}</div></div>")
        html.append(f"<div class='card'><h3>Informativos</h3><div class='value val-info'>{report.info_count}</div></div>")
        html.append(f"<div class='card'><h3>Duração</h3><div class='value val-time'>{report.total_duration_seconds:.1f}s</div></div>")
        html.append("</div>")

        # Seção de Conclusões e Causas Raiz
        if report.findings:
            html.append("<div class='findings-box'>")
            html.append("<h2>🩺 Diagnóstico de Causas Raiz Identificadas</h2>")
            for f in report.findings:
                html.append(f"<div class='finding-item {f.severity}'>")
                html.append(f"<div class='finding-title'><span class='finding-badge {f.severity}'>{f.severity.upper()}</span>{f.title}</div>")
                if f.evidence:
                    html.append(f"<div class='finding-field'><strong>Evidência medida:</strong> {f.evidence}</div>")
                if f.impact:
                    html.append(f"<div class='finding-field'><strong>Por que o aparelho trava/fica lento:</strong> {f.impact}</div>")
                if f.action:
                    html.append(f"<div class='finding-field'><strong>Ação recomendada:</strong> {f.action}</div>")
                html.append("</div>")
            html.append("</div>")

        # Agrupar testes por categoria
        categories: Dict[str, list] = {}
        for r in report.results:
            categories.setdefault(r.category, []).append(r)

        cat_names = {
            "memory": "Memória RAM & Swap",
            "cpu": "Processador (CPU)",
            "storage": "Armazenamento & Disco",
            "battery": "Bateria & Energia",
            "thermal": "Térmico",
            "display": "Tela & Display",
            "sensors": "Sensores",
            "network": "Rede & Wi-Fi",
            "system": "Sistema & Segurança",
            "apps": "Aplicativos",
            "processes": "Processos & Falhas"
        }

        for cat, results in categories.items():
            cat_label = cat_names.get(cat, cat.upper())
            html.append(f"<div class='category'><h2>{cat_label}</h2>")
            for res in results:
                status_str = res.status.value if hasattr(res.status, "value") else str(res.status)
                html.append(f"""
                <div class='test-row'>
                    <div class='test-info'>
                        <h4>{res.name}</h4>
                        <p>{res.message or ''}</p>
                    </div>
                    <div class='pill {status_str}'>{status_str}</div>
                </div>
                """)
            html.append("</div>")

        html.append("</div></body></html>")

        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write("\n".join(html))

        return out_p

    def generate_json(self, report: DiagnosticReport, output_path: Union[Path, str]) -> Path:
        """
        Exporta o relatório para JSON.
        """
        out_p = Path(output_path)
        data = {
            "device_serial": report.device_serial,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "overall_score": report.overall_score,
            "summary": report.summary,
            "counts": {
                "passed": report.passed_count,
                "warning": report.warning_count,
                "failed": report.failed_count,
                "info": report.info_count,
                "skipped": report.skipped_count,
            },
            "findings": [
                {
                    "severity": f.severity,
                    "title": f.title,
                    "evidence": f.evidence,
                    "impact": f.impact,
                    "action": f.action,
                    "tests": f.tests
                } for f in report.findings
            ],
            "duration_seconds": report.total_duration_seconds,
            "results": []
        }

        for r in report.results:
            status_str = r.status.value if hasattr(r.status, "value") else str(r.status)
            data["results"].append({
                "test_id": r.test_id,
                "name": r.name,
                "category": r.category,
                "status": status_str,
                "message": r.message,
                "details": r.details,
                "duration_ms": r.duration_ms
            })

        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return out_p
