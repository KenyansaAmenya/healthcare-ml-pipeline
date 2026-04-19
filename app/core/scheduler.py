import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.training_service import TrainingService

logger = logging.getLogger(__name__)


class ModelRetrainingScheduler:
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.training_service = TrainingService()
    
    def start(self):
        trigger = CronTrigger(
            day_of_week=settings.retrain_day,
            hour=settings.retrain_hour,
            minute=settings.retrain_minute
        )
        
        self.scheduler.add_job(
            self._retrain_job,
            trigger=trigger,
            id="model_retrain",
            name="Weekly Model Retraining",
            replace_existing=True
        )
        
        self.scheduler.start()
        next_run = self.scheduler.get_job("model_retrain").next_run_time
        logger.info(f"Scheduler started. Next retraining: {next_run}")
    
    async def _retrain_job(self):
        logger.info(f"Starting scheduled model retraining at {datetime.now()}")
        try:
            metrics = await self.training_service.retrain_model()
            logger.info(f"Retraining completed. Metrics: {metrics}")
        except Exception as e:
            logger.error(f"Retraining failed: {str(e)}")
    
    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("Scheduler shutdown complete")


scheduler = ModelRetrainingScheduler()