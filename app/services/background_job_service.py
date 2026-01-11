"""
Background Job Service
======================
Service layer for managing background jobs.

This service provides:
1. Job scheduling with idempotency
2. Job execution with retry logic
3. Dead letter queue management
4. Job status queries
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Callable, Dict
import traceback
import logging

from app import db
from app.models.background_job_models import (
    BackgroundJob, JobExecutionLog, IdempotencyRecord,
    JobStatus, JobType
)

logger = logging.getLogger(__name__)


class BackgroundJobService:
    """
    Service for scheduling and managing background jobs.
    """

    # Registry of job handlers
    _handlers: Dict[str, Callable] = {}

    @classmethod
    def register_handler(cls, job_type: str, handler: Callable):
        """
        Register a handler function for a job type.

        Args:
            job_type: The job type constant
            handler: A callable that takes (job, payload) and returns dict result
        """
        cls._handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    @classmethod
    def get_handler(cls, job_type: str) -> Optional[Callable]:
        """Get the registered handler for a job type"""
        return cls._handlers.get(job_type)

    @staticmethod
    def schedule_job(
        job_type: str,
        payload: dict = None,
        scheduled_at: datetime = None,
        idempotency_key: str = None,
        restaurant_id: int = None,
        subscription_id: int = None,
        order_id: int = None,
        priority: int = 5,
        max_retries: int = 3,
        retry_delay_seconds: int = 300,
        job_name: str = None
    ) -> Tuple[BackgroundJob, bool]:
        """
        Schedule a new background job.

        Args:
            job_type: Type of job (use JobType constants)
            payload: Job payload data
            scheduled_at: When to run the job (default: now)
            idempotency_key: Unique key to prevent duplicates
            restaurant_id: Associated restaurant
            subscription_id: Associated subscription
            order_id: Associated order
            priority: Job priority (1=highest, 10=lowest)
            max_retries: Maximum retry attempts
            retry_delay_seconds: Base delay between retries
            job_name: Human readable name

        Returns:
            Tuple of (BackgroundJob, was_created: bool)
        """
        # Check idempotency
        if idempotency_key:
            existing = BackgroundJob.query.filter_by(idempotency_key=idempotency_key).first()
            if existing:
                logger.info(f"Job already exists with idempotency key: {idempotency_key}")
                return existing, False

        # Create job
        job = BackgroundJob(
            job_type=job_type,
            job_name=job_name or job_type,
            idempotency_key=idempotency_key,
            scheduled_at=scheduled_at or datetime.utcnow(),
            restaurant_id=restaurant_id,
            subscription_id=subscription_id,
            order_id=order_id,
            priority=priority,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            status=JobStatus.SCHEDULED if scheduled_at and scheduled_at > datetime.utcnow() else JobStatus.PENDING
        )

        if payload:
            job.set_payload(payload)

        db.session.add(job)
        db.session.commit()

        logger.info(f"Scheduled job {job.job_id} of type {job_type}")
        return job, True

    @staticmethod
    def get_pending_jobs(limit: int = 100, job_types: List[str] = None) -> List[BackgroundJob]:
        """
        Get jobs that are ready to be processed.

        This includes:
        - Jobs with status 'pending' and scheduled_at <= now
        - Jobs with status 'retrying' and next_retry_at <= now
        - Jobs with status 'scheduled' and scheduled_at <= now

        Args:
            limit: Maximum number of jobs to return
            job_types: Optional list of job types to filter

        Returns:
            List of jobs ready for processing
        """
        now = datetime.utcnow()

        query = BackgroundJob.query.filter(
            db.or_(
                # Pending jobs ready to run
                db.and_(
                    BackgroundJob.status == JobStatus.PENDING,
                    BackgroundJob.scheduled_at <= now
                ),
                # Scheduled jobs ready to run
                db.and_(
                    BackgroundJob.status == JobStatus.SCHEDULED,
                    BackgroundJob.scheduled_at <= now
                ),
                # Jobs ready for retry
                db.and_(
                    BackgroundJob.status == JobStatus.RETRYING,
                    BackgroundJob.next_retry_at <= now
                )
            ),
            # Not locked or lock expired
            db.or_(
                BackgroundJob.locked_by.is_(None),
                BackgroundJob.lock_expires_at <= now
            )
        )

        if job_types:
            query = query.filter(BackgroundJob.job_type.in_(job_types))

        return query.order_by(
            BackgroundJob.priority.asc(),
            BackgroundJob.scheduled_at.asc()
        ).limit(limit).all()

    @staticmethod
    def acquire_job(job_id: int, worker_id: str) -> Optional[BackgroundJob]:
        """
        Try to acquire a lock on a job for processing.

        Uses optimistic locking to prevent race conditions.

        Args:
            job_id: The job's database ID
            worker_id: The worker attempting to acquire

        Returns:
            The job if acquired, None if not available
        """
        now = datetime.utcnow()

        # Use update with conditions for atomic lock
        result = BackgroundJob.query.filter(
            BackgroundJob.id == job_id,
            BackgroundJob.status.in_([JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.RETRYING]),
            db.or_(
                BackgroundJob.locked_by.is_(None),
                BackgroundJob.lock_expires_at <= now
            )
        ).update({
            'status': JobStatus.PROCESSING,
            'locked_by': worker_id,
            'locked_at': now,
            'lock_expires_at': now + timedelta(minutes=30),
            'started_at': now
        }, synchronize_session=False)

        db.session.commit()

        if result > 0:
            return BackgroundJob.query.get(job_id)
        return None

    @staticmethod
    def execute_job(job: BackgroundJob, worker_id: str = 'default') -> bool:
        """
        Execute a job using its registered handler.

        Args:
            job: The job to execute
            worker_id: The worker executing this job

        Returns:
            True if successful, False otherwise
        """
        # Create execution log
        log = JobExecutionLog(
            job_id=job.id,
            attempt_number=job.retry_count + 1,
            worker_id=worker_id,
            status='started',
            input_data=job.payload
        )
        db.session.add(log)
        db.session.commit()

        try:
            # Get handler
            handler = BackgroundJobService.get_handler(job.job_type)
            if not handler:
                raise ValueError(f"No handler registered for job type: {job.job_type}")

            # Execute handler
            payload = job.get_payload()
            result = handler(job, payload)

            # Mark success
            job.mark_completed(result or {})
            log.set_ended(True, output=result)

            db.session.commit()
            logger.info(f"Job {job.job_id} completed successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()

            job.mark_failed(error_msg, error_trace)
            log.set_ended(False, error=error_msg, trace=error_trace)

            db.session.commit()

            if job.status == JobStatus.DEAD:
                logger.error(f"Job {job.job_id} moved to dead letter queue: {error_msg}")
            else:
                logger.warning(f"Job {job.job_id} failed, will retry: {error_msg}")

            return False

    @staticmethod
    def cancel_job(job_id: int) -> bool:
        """Cancel a pending or scheduled job"""
        job = BackgroundJob.query.get(job_id)
        if not job:
            return False

        if job.status not in [JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.RETRYING]:
            return False

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Job {job.job_id} cancelled")
        return True

    @staticmethod
    def retry_dead_job(job_id: int) -> bool:
        """Manually retry a dead letter job"""
        job = BackgroundJob.query.get(job_id)
        if not job:
            return False

        if job.status != JobStatus.DEAD:
            return False

        job.status = JobStatus.PENDING
        job.retry_count = 0
        job.scheduled_at = datetime.utcnow()
        job.error_message = None
        job.error_trace = None
        job.result = None
        job.completed_at = None
        db.session.commit()

        logger.info(f"Job {job.job_id} reset for retry")
        return True

    @staticmethod
    def get_job_stats(restaurant_id: int = None) -> dict:
        """Get job statistics"""
        query = db.session.query(
            BackgroundJob.status,
            db.func.count(BackgroundJob.id)
        )

        if restaurant_id:
            query = query.filter(BackgroundJob.restaurant_id == restaurant_id)

        results = query.group_by(BackgroundJob.status).all()

        stats = {status: 0 for status in [
            JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.PROCESSING,
            JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.RETRYING,
            JobStatus.DEAD, JobStatus.CANCELLED
        ]}

        for status, count in results:
            stats[status] = count

        # Get recent failures
        recent_failures = BackgroundJob.query.filter(
            BackgroundJob.status.in_([JobStatus.FAILED, JobStatus.DEAD]),
            BackgroundJob.updated_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()

        stats['total'] = sum(stats.values())
        stats['recent_failures_24h'] = recent_failures

        return stats

    @staticmethod
    def get_dead_letter_jobs(limit: int = 50) -> List[BackgroundJob]:
        """Get jobs in the dead letter queue"""
        return BackgroundJob.query.filter(
            BackgroundJob.status == JobStatus.DEAD
        ).order_by(
            BackgroundJob.completed_at.desc()
        ).limit(limit).all()

    @staticmethod
    def cleanup_old_jobs(days: int = 30) -> int:
        """
        Clean up completed/cancelled jobs older than specified days.

        Returns the number of jobs deleted.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # First delete execution logs
        log_result = JobExecutionLog.query.filter(
            JobExecutionLog.job_id.in_(
                db.session.query(BackgroundJob.id).filter(
                    BackgroundJob.status.in_([JobStatus.COMPLETED, JobStatus.CANCELLED]),
                    BackgroundJob.completed_at < cutoff
                )
            )
        ).delete(synchronize_session=False)

        # Then delete jobs
        result = BackgroundJob.query.filter(
            BackgroundJob.status.in_([JobStatus.COMPLETED, JobStatus.CANCELLED]),
            BackgroundJob.completed_at < cutoff
        ).delete(synchronize_session=False)

        db.session.commit()
        logger.info(f"Cleaned up {result} old jobs and {log_result} execution logs")

        return result


# ===========================================
# JOB SCHEDULER - Entry points for scheduling common jobs
# ===========================================

class JobScheduler:
    """
    Convenience class for scheduling common job types.
    """

    @staticmethod
    def schedule_trial_expiration(subscription_id: int, trial_end_date: datetime, restaurant_id: int) -> BackgroundJob:
        """Schedule a trial expiration check"""
        idempotency_key = f"{JobType.TRIAL_EXPIRATION}:{subscription_id}:{trial_end_date.date()}"

        job, _ = BackgroundJobService.schedule_job(
            job_type=JobType.TRIAL_EXPIRATION,
            job_name=f"Trial Expiration Check - Subscription {subscription_id}",
            scheduled_at=trial_end_date,
            idempotency_key=idempotency_key,
            subscription_id=subscription_id,
            restaurant_id=restaurant_id,
            payload={
                'subscription_id': subscription_id,
                'trial_end_date': trial_end_date.isoformat()
            },
            priority=2
        )
        return job

    @staticmethod
    def schedule_trial_reminder(subscription_id: int, reminder_date: datetime, days_remaining: int, restaurant_id: int) -> BackgroundJob:
        """Schedule a trial ending reminder"""
        idempotency_key = f"{JobType.SUBSCRIPTION_REMINDER}:trial:{subscription_id}:{reminder_date.date()}"

        job, _ = BackgroundJobService.schedule_job(
            job_type=JobType.SUBSCRIPTION_REMINDER,
            job_name=f"Trial Reminder ({days_remaining} days) - Subscription {subscription_id}",
            scheduled_at=reminder_date,
            idempotency_key=idempotency_key,
            subscription_id=subscription_id,
            restaurant_id=restaurant_id,
            payload={
                'subscription_id': subscription_id,
                'reminder_type': 'trial_ending',
                'days_remaining': days_remaining
            },
            priority=3
        )
        return job

    @staticmethod
    def schedule_subscription_renewal(subscription_id: int, renewal_date: datetime, restaurant_id: int) -> BackgroundJob:
        """Schedule a subscription renewal"""
        idempotency_key = f"{JobType.SUBSCRIPTION_RENEWAL}:{subscription_id}:{renewal_date.date()}"

        job, _ = BackgroundJobService.schedule_job(
            job_type=JobType.SUBSCRIPTION_RENEWAL,
            job_name=f"Subscription Renewal - Subscription {subscription_id}",
            scheduled_at=renewal_date,
            idempotency_key=idempotency_key,
            subscription_id=subscription_id,
            restaurant_id=restaurant_id,
            payload={
                'subscription_id': subscription_id,
                'renewal_date': renewal_date.isoformat()
            },
            priority=1,
            max_retries=5  # More retries for billing
        )
        return job

    @staticmethod
    def schedule_payment_retry(subscription_id: int, retry_date: datetime, attempt: int, restaurant_id: int) -> BackgroundJob:
        """Schedule a payment retry"""
        idempotency_key = f"{JobType.PAYMENT_RETRY}:{subscription_id}:{retry_date.date()}:{attempt}"

        job, _ = BackgroundJobService.schedule_job(
            job_type=JobType.PAYMENT_RETRY,
            job_name=f"Payment Retry (Attempt {attempt}) - Subscription {subscription_id}",
            scheduled_at=retry_date,
            idempotency_key=idempotency_key,
            subscription_id=subscription_id,
            restaurant_id=restaurant_id,
            payload={
                'subscription_id': subscription_id,
                'attempt': attempt,
                'retry_date': retry_date.isoformat()
            },
            priority=1
        )
        return job

    @staticmethod
    def schedule_order_number_cleanup(restaurant_id: int, scheduled_at: datetime = None) -> BackgroundJob:
        """Schedule cleanup of recycled display order numbers"""
        if not scheduled_at:
            scheduled_at = datetime.utcnow()

        # Only one cleanup per restaurant per day
        idempotency_key = f"{JobType.ORDER_CLEANUP}:{restaurant_id}:{scheduled_at.date()}"

        job, _ = BackgroundJobService.schedule_job(
            job_type=JobType.ORDER_CLEANUP,
            job_name=f"Order Number Cleanup - Restaurant {restaurant_id}",
            scheduled_at=scheduled_at,
            idempotency_key=idempotency_key,
            restaurant_id=restaurant_id,
            payload={
                'restaurant_id': restaurant_id
            },
            priority=8  # Lower priority maintenance task
        )
        return job

    @staticmethod
    def schedule_grace_period_check(subscription_id: int, check_date: datetime, restaurant_id: int) -> BackgroundJob:
        """Schedule grace period expiration check"""
        idempotency_key = f"{JobType.GRACE_PERIOD_CHECK}:{subscription_id}:{check_date.date()}"

        job, _ = BackgroundJobService.schedule_job(
            job_type=JobType.GRACE_PERIOD_CHECK,
            job_name=f"Grace Period Check - Subscription {subscription_id}",
            scheduled_at=check_date,
            idempotency_key=idempotency_key,
            subscription_id=subscription_id,
            restaurant_id=restaurant_id,
            payload={
                'subscription_id': subscription_id,
                'check_date': check_date.isoformat()
            },
            priority=2
        )
        return job

