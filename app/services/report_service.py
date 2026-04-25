from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from zoneinfo import ZoneInfo

from app.config import AppConfig
from app.constants import LOCALIZA_NAME, MOVIDA_NAME
from app.models import CarOption, QuoteRequest, QuoteResult, RunSummary
from app.utils.formatters import format_brl


class ReportService:
    def __init__(self, config: AppConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger

    @staticmethod
    def select_cheapest_options(options: Sequence[CarOption], limit: int = 3) -> list[CarOption]:
        ranked = sorted(
            options,
            key=lambda item: (item.total_price is None, item.total_price if item.total_price is not None else float("inf")),
        )
        return list(ranked[:limit])

    def build_run_summary(
        self,
        localiza: QuoteResult,
        movida: QuoteResult,
        errors: list[str] | None = None,
    ) -> RunSummary:
        executed_at = datetime.now(ZoneInfo(self.config.timezone)).strftime("%d/%m/%Y %H:%M:%S")
        return RunSummary(
            request=self.config.quote_request,
            localiza=localiza,
            movida=movida,
            errors=errors or [],
            executed_at=executed_at,
        )

    def build_telegram_message(self, summary: RunSummary) -> str:
        if not summary.localiza.success and not summary.movida.success:
            lines = [
                "🚗 Cotacao diaria - Aeroporto de Porto Seguro/BA",
                f"📅 Retirada: {summary.request.pickup_date} {summary.request.pickup_time}",
                f"📅 Devolucao: {summary.request.return_date} {summary.request.return_time}",
                "",
                "⚠️ Nenhuma locadora retornou cotacao valida hoje.",
                f"- {LOCALIZA_NAME}: {summary.localiza.error or 'falha sem detalhe'}",
                f"- {MOVIDA_NAME}: {summary.movida.error or 'falha sem detalhe'}",
            ]
            if summary.errors:
                lines.extend(["", "Observacoes:"])
                lines.extend(f"- {error}" for error in summary.errors)
            lines.append("")
            lines.append(f"🕒 Coletado em: {summary.executed_at}")
            return "\n".join(lines)

        lines = [
            "🚗 Cotacao diaria - Aeroporto de Porto Seguro/BA",
            f"📅 Retirada: {summary.request.pickup_date} {summary.request.pickup_time}",
            f"📅 Devolucao: {summary.request.return_date} {summary.request.return_time}",
            "",
        ]

        lines.extend(self._build_provider_block(summary.localiza))
        lines.append("")
        lines.extend(self._build_provider_block(summary.movida))

        observations = list(summary.errors)
        observations.extend(summary.localiza.observations)
        observations.extend(summary.movida.observations)

        if observations:
            lines.extend(["", "⚠️ Observacoes:"])
            for observation in observations:
                lines.append(f"- {observation}")

        lines.extend(["", f"🕒 Coletado em: {summary.executed_at}"])
        return "\n".join(lines)

    def _build_provider_block(self, result: QuoteResult) -> list[str]:
        lines = [f"🏢 {result.provider}"]
        lines.append(f"Agencia: {result.agency_name or 'Nao identificada'}")

        if result.success and result.options:
            for index, option in enumerate(self.select_cheapest_options(result.options), start=1):
                title = option.name
                if option.group:
                    title = f"{title} / {option.group}"
                price_text = option.total_price_text or format_brl(option.total_price)
                lines.append(f"{index}. {title} — {price_text}")
        else:
            lines.append(f"Falha: {result.error or 'cotacao invalida'}")
        return lines

    def build_markdown_report(self, summary: RunSummary) -> str:
        blocks = [
            "# Cotacao diaria de aluguel de carros",
            "",
            f"- Retirada: {summary.request.pickup_date} {summary.request.pickup_time}",
            f"- Devolucao: {summary.request.return_date} {summary.request.return_time}",
            f"- Local: {summary.request.pickup_location}",
            f"- Executado em: {summary.executed_at}",
            "",
        ]

        for result in (summary.localiza, summary.movida):
            blocks.append(f"## {result.provider}")
            blocks.append(f"- Sucesso: {'sim' if result.success else 'nao'}")
            blocks.append(f"- Agencia: {result.agency_name or 'Nao identificada'}")
            blocks.append(f"- Agencia validada como aeroporto: {'sim' if result.airport_validated else 'nao'}")
            blocks.append(f"- Extras desmarcados/nao selecionados: {result.addons_cleared}")
            blocks.append(f"- URL final: {result.final_url or 'N/A'}")
            if result.error:
                blocks.append(f"- Erro: {result.error}")
            for observation in result.observations:
                blocks.append(f"- Observacao: {observation}")
            if result.options:
                blocks.append("")
                for option in self.select_cheapest_options(result.options):
                    blocks.append(
                        f"- {option.name} | {option.group or 'grupo n/d'} | "
                        f"{option.total_price_text or format_brl(option.total_price)}"
                    )
            blocks.append("")

        if summary.errors:
            blocks.append("## Erros gerais")
            for error in summary.errors:
                blocks.append(f"- {error}")
            blocks.append("")

        return "\n".join(blocks).strip() + "\n"

    def persist_outputs(self, summary: RunSummary) -> None:
        self.config.latest_json_file.write_text(
            json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.config.latest_markdown_file.write_text(
            self.build_markdown_report(summary),
            encoding="utf-8",
        )
        self.logger.info(
            "Arquivos de saida atualizados: %s e %s",
            self.config.latest_json_file,
            self.config.latest_markdown_file,
        )
