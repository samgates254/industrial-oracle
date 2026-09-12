"""RFC 8259 JSON serialization for DiagnosticReport."""

import json
from dataclasses import fields, is_dataclass
from typing import Any, Dict
from industrial_oracle.diagnostics.report import DiagnosticReport


def _clean_for_json(obj: Any) -> Any:
    """Recursively convert dataclasses, MappingProxyType, and tuples into JSON-serializable primitives without using asdict (which fails on mappingproxy)."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _clean_for_json(getattr(obj, f.name))
            for f in fields(obj)
        }
    elif isinstance(obj, dict) or hasattr(obj, 'items'):
        return {str(k): _clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_clean_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if obj == float('inf'):
            return 'Infinity'
        elif obj == float('-inf'):
            return '-Infinity'
        return obj
    return obj


def serialize_diagnostic_report_to_dict(report: DiagnosticReport) -> Dict[str, Any]:
    """Convert DiagnosticReport to standard nested dictionary."""
    return _clean_for_json(report)


def serialize_diagnostic_report_to_json(report: DiagnosticReport, indent: int = 2) -> str:
    """Serialize DiagnosticReport into formatted JSON string."""
    data = serialize_diagnostic_report_to_dict(report)
    return json.dumps(data, indent=indent)
