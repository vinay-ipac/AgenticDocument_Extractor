"""Agent components for document analysis."""

from .tools import (
    AnalyzeTable,
    AnalyzeTableHindi,
    AnalyzeForm,
    AnalyzeStamp,
    AnalyzeChart,
    create_vlm_tools,
)
from .prompts import (
    SYSTEM_PROMPT,
    TABLE_ANALYSIS_PROMPT,
    TABLE_HINDI_PROMPT,
    FORM_ANALYSIS_PROMPT,
    STAMP_ANALYSIS_PROMPT,
    CHART_ANALYSIS_PROMPT,
)
from .orchestrator import AgentOrchestrator

__all__ = [
    "AnalyzeTable",
    "AnalyzeTableHindi",
    "AnalyzeForm",
    "AnalyzeStamp",
    "AnalyzeChart",
    "create_vlm_tools",
    "SYSTEM_PROMPT",
    "TABLE_ANALYSIS_PROMPT",
    "TABLE_HINDI_PROMPT",
    "FORM_ANALYSIS_PROMPT",
    "STAMP_ANALYSIS_PROMPT",
    "CHART_ANALYSIS_PROMPT",
    "AgentOrchestrator",
]
