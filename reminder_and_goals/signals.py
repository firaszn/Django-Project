# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Reminder
import logging

logger = logging.getLogger(__name__)

try:
    from .services.apple_reminders_service import get_apple_reminders_service_for_user
    CALDAV_AVAILABLE = True
    logger.info("Apple reminders service imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Apple reminders service: {e}")
    CALDAV_AVAILABLE = False
except Exception as e:
    logger.error(f"Unexpected error importing Apple service: {e}")
    CALDAV_AVAILABLE = False

@receiver(post_save, sender=Reminder)
def sync_reminder_with_apple(sender, instance, created, **kwargs):
    """Sync reminder with Apple Reminders when created or updated"""
    logger.info(f"Signal triggered for Reminder {instance.id}, created: {created}")
    
    if not instance.status:
        logger.info(f"Reminder {instance.id} is not active, skipping Apple sync")
        return
    
    if not CALDAV_AVAILABLE:
        logger.error("CALDAV_AVAILABLE is False - service not available")
        return
    
    logger.info(f"Signal conditions met for Reminder {instance.id}")
    
    try:
        # Check if user has Apple account connected
        logger.info(f"Getting Apple service for user: {instance.user}")
        apple_service = get_apple_reminders_service_for_user(instance.user)
        
        if not apple_service:
            logger.warning(f"No Apple service configured for user {instance.user}")
            return
        
        logger.info(f"Apple service obtained for user {instance.user}")
        
        if created:
            logger.info(f"Creating new Apple reminder for {instance.id}")
            apple_id = apple_service.create_reminder(instance)
            if apple_id:
                logger.info(f"Successfully created Apple reminder with ID: {apple_id}")
                # Force refresh and check
                instance.refresh_from_db()
                logger.info(f"After sync - apple_reminder_id: {instance.apple_reminder_id}, is_synced: {instance.is_synced_with_apple}")
            else:
                logger.error(f"Failed to create Apple reminder for {instance.id}")
                
    except Exception as e:
        logger.error(f"Error in signal for reminder {instance.id}: {e}", exc_info=True)

logger.info("Reminder signals module loaded")