"""Phase 3: Integration - Data Storage, Automation, Dashboard"""

from phase3_integration.datastore import get_datastore, PersonDataStore, PersonProfile
from phase3_integration.automation import ResearchAutomationEngine, create_n8n_webhook_handler
from phase3_integration.dashboard import app, run_dashboard

__all__ = [
    "get_datastore",
    "PersonDataStore",
    "PersonProfile",
    "ResearchAutomationEngine",
    "create_n8n_webhook_handler",
    "app",
    "run_dashboard"
]
