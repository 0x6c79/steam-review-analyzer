import logging
from typing import List, Dict, Callable, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


class AlertRule:
    def __init__(self, name: str, condition: str, threshold: float, message: str):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.message = message
        
    def evaluate(self, stats: Dict) -> Optional[str]:
        value = None
        
        if self.condition == "positive_rate_below":
            if stats.get('total', 0) > 0:
                value = stats['positive'] / stats['total']
                if value < self.threshold:
                    return self.message.format(rate=value*100)
                    
        elif self.condition == "negative_reviews_spike":
            recent = stats.get('recent_negative', 0)
            avg = stats.get('avg_negative', 1)
            if recent > avg * self.threshold:
                return self.message.format(recent=recent, avg=avg)
                
        elif self.condition == "total_reviews_below":
            if stats.get('total', 0) < self.threshold:
                return self.message.format(total=stats.get('total', 0))
                
        return None


class AlertManager:
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.handlers: List[Callable] = []
        self.alert_history: List[Dict] = []
        
    def add_rule(self, name: str, condition: str, threshold: float, message: str):
        rule = AlertRule(name, condition, threshold, message)
        self.rules.append(rule)
        logger.info(f"Added alert rule: {name}")
        
    def add_handler(self, handler: Callable):
        self.handlers.append(handler)
        
    def check(self, stats: Dict) -> List[str]:
        alerts = []
        
        for rule in self.rules:
            result = rule.evaluate(stats)
            if result:
                alerts.append(result)
                self._record_alert(rule.name, result, stats)
                
        for alert in alerts:
            for handler in self.handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
                    
        return alerts
    
    def _record_alert(self, rule_name: str, message: str, stats: Dict):
        record = {
            "timestamp": datetime.now().isoformat(),
            "rule": rule_name,
            "message": message,
            "stats": stats
        }
        self.alert_history.append(record)
        
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]


class ConsoleAlertHandler:
    def __init__(self):
        pass
        
    def __call__(self, alert: str):
        logger.warning(f"ALERT: {alert}")


class FileAlertHandler:
    def __init__(self, filepath: str = "alerts.log"):
        self.filepath = filepath
        
    def __call__(self, alert: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, 'a') as f:
            f.write(f"[{timestamp}] {alert}\n")


class SlackAlertHandler:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        
    def __call__(self, alert: str):
        if not self.webhook_url:
            logger.warning("Slack webhook not configured")
            return
            
        try:
            import requests
            requests.post(self.webhook_url, json={"text": f"Steam Review Alert: {alert}"})
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")


def create_default_alert_manager() -> AlertManager:
    manager = AlertManager()
    
    manager.add_rule(
        "low_rating",
        "positive_rate_below",
        0.5,
        "Warning: Positive rate ({rate:.1f}%) dropped below 50%"
    )
    
    manager.add_rule(
        "negative_spike",
        "negative_reviews_spike",
        2.0,
        "Warning: Negative reviews spike detected (recent: {recent}, avg: {avg:.1f})"
    )
    
    manager.add_rule(
        "no_reviews",
        "total_reviews_below",
        10,
        "Warning: Very few reviews collected ({total})"
    )
    
    manager.add_handler(ConsoleAlertHandler())
    manager.add_handler(FileAlertHandler())
    
    return manager


def check_and_alert(stats: Dict, manager: AlertManager = None) -> List[str]:
    if manager is None:
        manager = create_default_alert_manager()
        
    return manager.check(stats)
