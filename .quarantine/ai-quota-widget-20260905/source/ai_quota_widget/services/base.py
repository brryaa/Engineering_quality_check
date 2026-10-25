import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class QuotaResult:
    service_id: str
    service_name: str
    status: str  # 'ok', 'warning', 'error', 'unauthorized'
    status_text: str
    tier: str  # e.g., "Plus", "X Premium+", "Standard Tier"
    
    # Dual-dimension controls
    has_short_term: bool = True
    short_term_label: str = "5小时余量"
    short_term_metric: str = "--"
    short_term_pct: float = 100.0
    
    long_term_label: str = "一周余量"
    long_term_metric: str = "--"
    long_term_pct: float = 100.0

    # Summary metrics (for compatibility and mini view)
    primary_metric: str = ""
    secondary_metric: str = ""
    percentage: float = 100.0

    details: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.primary_metric:
            self.primary_metric = self.short_term_metric if self.has_short_term else self.long_term_metric
        if self.percentage == 100.0 and self.long_term_pct != 100.0:
            self.percentage = self.long_term_pct if not self.has_short_term else self.short_term_pct

    @property
    def formatted_time(self) -> str:
        return time.strftime("%H:%M:%S", time.localtime(self.last_updated))


class BaseService:
    def __init__(self, service_id: str, service_name: str, config_manager):
        self.service_id = service_id
        self.service_name = service_name
        self.config_manager = config_manager

    def fetch_quota(self) -> QuotaResult:
        raise NotImplementedError

    def get_auth_info(self) -> Dict[str, Any]:
        return self.config_manager.get_service_config(self.service_id)

    def set_auth(self, **kwargs):
        self.config_manager.update_service_config(self.service_id, kwargs)
