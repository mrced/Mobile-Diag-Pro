import json
from pathlib import Path
from dataclasses import asdict

from core.diagnostic_engine import DiagnosticReport, TestStatus


class ReportGenerator:
    """
    Gerador de relatórios visuais (HTML) e analíticos (JSON).
    Gera relatórios bonitos e responsivos com estilo Dark/Light da Apple (macOS style).
    """

    def _get_css(self) -> str:
        """
        Retorna o CSS injetado no relatório HTML.
        """
        return """
        :root {
            --bg-color: #1e1e1e;
            --surface-color: #2d2d2d;
            --text-primary: #e0e0e0;
            --text-secondary: #aaaaaa;
            --accent-color: #0A84FF;
            --pass-color: #30d158;
            --warn-color: #ffd60a;
            --fail-color: #ff453a;
            --border-color: #3a3a3a;
        }
        @media (prefers-color-scheme: light) {
            :root {
                --bg-color: #f5f5f7;
                --surface-color: #ffffff;
                --text-primary: #1d1d1f;
                --text-secondary: #86868b;
                --accent-color: #007aff;
                --pass-color: #34c759;
                --warn-color: #ffcc00;
                --fail-color: #ff3b30;
                --border-color: #d2d2d7;
            }
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .score-badge {
            display: inline-block;
            font-size: 3em;
            font-weight: 700;
            padding: 10px 30px;
            border-radius: 50px;
            background-color: var(--surface-color);
            border: 2px solid var(--accent-color);
            color: var(--accent-color);
            margin-top: 10px;
        }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        .card {
            background-color: var(--surface-color);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h3 { margin: 0; font-size: 0.9em; color: var(--text-secondary); text-transform: uppercase; }
        .card .value { font-size: 2em; font-weight: bold; margin-top: 10px; }
        .val-pass { color: var(--pass-color); }
        .val-warn { color: var(--warn-color); }
        .val-fail { color: var(--fail-color); }
        .val-time { color: var(--text-primary); }
        
        .category {
            background-color: var(--surface-color);
            border-radius: 12px;
            margin-bottom: 20px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .category h2 {
            margin-top: 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            text-transform: capitalize;
        }
        .test-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
        }
        .test-row:last-child {
            border-bottom: none;
        }
        .test-info h4 { margin: 0 0 5px 0; }
        .test-info p { margin: 0; font-size: 0.85em; color: var(--text-secondary); }
        .pill {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .pill.passed { background-color: rgba(52, 199, 89, 0.2); color: var(--pass-color); }
        .pill.warning { background-color: rgba(255, 204, 0, 0.2); color: var(--warn-color); }
        .pill.failed { background-color: rgba(255, 59, 48, 0.2); color: var(--fail-color); }
        .pill.skipped { background-color: rgba(142, 142, 147, 0.2); color: var(--text-secondary); }
        
        .recommendations {
            background-color: var(--surface-color);
            border-radius: 12px;
            padding: 20px;
            border-left: 5px solid var(--warn-color);
            margin-top: 30px;
        }
        .recommendations ul { margin: 0; padding-left: 20px; }
        .recommendations li { margin-bottom: 10px; }

        @media print {
            body { background-color: white; color: black; }
            .card, .category, .recommendations { box-shadow: none; border: 1px solid #ccc; }
        }
        """

    def generate_html(self, report: DiagnosticReport, device_info: dict, output_path: Path) -> Path:
        """
        Gera um relatório HTML contendo o resultado dos diagnósticos.

        Args:
            report: O relatório gerado pelo DiagnosticEngine.
            device_info: Dicionário contendo dados do aparelho (ex. modelo, marca).
            output_path: Caminho de destino para salvar o arquivo HTML.

        Returns:
            Path: Caminho do arquivo gerado.
        """
        html = [
            "<!DOCTYPE html>",
            "<html lang='pt-BR'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Relatório de Diagnóstico - Mobile-Diag-Pro</title>",
            f"<style>{self._get_css()}</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            "<div class='header'>",
            "<h1>Relatório de Saúde do Dispositivo</h1>",
            f"<p>Serial: {report.device_serial} | Data: {report.end_time.strftime('%d/%m/%Y %H:%M:%S')}</p>"
        ]

        # Device info fallback (poderia ser formatado mais robusto)
        if device_info:
            html.append(f"<p>{device_info.get('model', 'Unknown')} - {device_info.get('brand', 'Unknown')}</p>")

        html.extend([
            f"<div class='score-badge'>{report.overall_score}/100</div>",
            "</div>",
            "<div class='summary-cards'>"
        ])

        html.append(f"<div class='card'><h3>Passed</h3><div class='value val-pass'>{report.passed_count}</div></div>")
        html.append(f"<div class='card'><h3>Warnings</h3><div class='value val-warn'>{report.warning_count}</div></div>")
        html.append(f"<div class='card'><h3>Failed</h3><div class='value val-fail'>{report.failed_count}</div></div>")
        html.append(f"<div class='card'><h3>Duration</h3><div class='value val-time'>{report.total_duration_seconds:.1f}s</div></div>")

        html.append("</div>")

        # Agrupar por categorias
        categories = {}
        for r in report.results:
            categories.setdefault(r.category, []).append(r)

        for cat, results in categories.items():
            html.append(f"<div class='category'><h2>{cat}</h2>")
            for res in results:
                html.append(f"""
                <div class='test-row'>
                    <div class='test-info'>
                        <h4>{res.name}</h4>
                        <p>{res.details}</p>
                    </div>
                    <div class='pill {res.status.value}'>{res.status.value}</div>
                </div>
                """)
            html.append("</div>")

        # Recomendações baseadas em warnings e falhas
        issues = [r for r in report.results if r.status in (TestStatus.WARNING, TestStatus.FAILED)]
        if issues:
            html.append("<div class='recommendations'>")
            html.append("<h2>Atenção Recomendada</h2><ul>")
            for issue in issues:
                html.append(f"<li><strong>{issue.name} ({issue.category}):</strong> Verificar falha reportada. Detalhes: {issue.details}</li>")
            html.append("</ul></div>")

        html.append("</div></body></html>")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))

        return output_path

    def generate_json(self, report: DiagnosticReport, output_path: Path) -> Path:
        """
        Exporta o relatório bruto para JSON para integrações futuras.

        Args:
            report: O relatório diagnóstico a ser exportado.
            output_path: Caminho do arquivo JSON de saída.

        Returns:
            Path: O caminho do arquivo gerado.
        """
        data = {
            "device_serial": report.device_serial,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "overall_score": report.overall_score,
            "counts": {
                "passed": report.passed_count,
                "warning": report.warning_count,
                "failed": report.failed_count,
                "skipped": report.skipped_count,
            },
            "duration_seconds": report.total_duration_seconds,
            "results": []
        }

        for r in report.results:
            data["results"].append({
                "test_id": r.test_id,
                "name": r.name,
                "category": r.category,
                "status": r.status.value,
                "details": r.details,
                "value": r.value,
                "duration_ms": r.duration_ms
            })

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return output_path
