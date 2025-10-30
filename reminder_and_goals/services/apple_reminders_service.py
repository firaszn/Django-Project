# services/apple_reminders_service.py
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AppleRemindersService:
    def __init__(self, username, password, webhook_url=None, webhook_secret=None):
        self.username = username
        self.password = password
        self.connected = False
        self._client = None
        self._principal = None
        self._calendar = None
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        # Use regular characters for logging to avoid encoding issues
        logger.info(f"AppleRemindersService initialized for user: {username}")
        logger.info(f"Password provided: {'YES' if password else 'NO'}")
        
    def connect(self):
        """Test connection to Apple services"""
        try:
            logger.info(f"Attempting to connect for user: {self.username}")
            logger.info(f"Password length: {len(self.password) if self.password else 0}")
            
            # Prefer real CalDAV connection if dependencies are available
            try:
                import caldav  # type: ignore
                caldav_available = True
            except Exception:
                caldav_available = False

            if self.username and self.password and caldav_available:
                try:
                    server_url = getattr(settings, 'APPLE_CALDAV_SERVER', 'https://caldav.icloud.com')
                    self._client = caldav.DAVClient(
                        url=server_url,
                        username=self.username,
                        password=self.password,
                    )
                    self._principal = self._client.principal()
                    # First preference: dedicated task lists (Reminders)
                    selected = None
                    try:
                        tasklists = getattr(self._principal, 'tasklists', None)
                        if callable(tasklists):
                            lists = tasklists()
                            if lists:
                                # Log discovered tasklists
                                try:
                                    for tl in lists:
                                        logger.info(f"Found tasklist: {getattr(tl, 'url', getattr(tl, 'href', 'unknown'))}")
                                except Exception:
                                    pass
                                selected = lists[0]
                                logger.info("Selected tasklist collection for reminders")
                    except Exception as e:
                        logger.warning(f"Failed to fetch tasklists: {e}")

                    # Second preference: calendars explicitly supporting VTODO
                    if selected is None:
                        calendars = []
                        try:
                            calendars = self._principal.calendars()
                            try:
                                for c in calendars:
                                    logger.info(f"Found calendar: {getattr(c, 'url', getattr(c, 'href', 'unknown'))}")
                            except Exception:
                                pass
                        except Exception as e:
                            logger.warning(f"Failed to fetch calendars: {e}")

                        for cal in calendars:
                            try:
                                name = None
                                try:
                                    props = cal.get_properties([
                                        '{DAV:}displayname',
                                        '{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set',
                                    ])
                                    name = str(props.get('{DAV:}displayname', ''))
                                    supported = props.get('{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set')
                                    components = []
                                    if supported is not None:
                                        try:
                                            components = [c.name if hasattr(c, 'name') else str(c) for c in supported.children]
                                        except Exception:
                                            components = []
                                    else:
                                        try:
                                            components = cal.get_supported_components()
                                        except Exception:
                                            components = []
                                except Exception:
                                    components = []
                                    name = None

                                if any(c for c in components if 'VTODO' in str(c).upper()):
                                    selected = cal
                                    logger.info(f"Selected VTODO-capable calendar collection: {name or '(unnamed)'}")
                                    break
                            except Exception:
                                continue

                    if selected is None:
                        # No VTODO list; select a VEVENT-capable calendar instead
                        calendars = []
                        try:
                            calendars = self._principal.calendars()
                        except Exception:
                            calendars = []
                        fallback_calendar = None
                        for cal in calendars:
                            try:
                                components = []
                                try:
                                    props = cal.get_properties([
                                        '{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set',
                                    ])
                                    supported = props.get('{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set')
                                    if supported is not None:
                                        components = [c.name if hasattr(c, 'name') else str(c) for c in supported.children]
                                except Exception:
                                    try:
                                        components = cal.get_supported_components()
                                    except Exception:
                                        components = []
                                if any('VEVENT' in str(c).upper() for c in components):
                                    fallback_calendar = cal
                                    break
                            except Exception:
                                continue
                        if fallback_calendar is None and calendars:
                            fallback_calendar = calendars[0]
                        if fallback_calendar is None:
                            logger.error("No calendar collection available for VEVENTs")
                        else:
                            self._calendar = fallback_calendar
                            logger.info("CalDAV calendar selected for events (VEVENT)")
                    else:
                        self._calendar = selected
                        logger.info("CalDAV collection selected for reminders")
                    self.connected = True
                    logger.info("Connection successful (CalDAV)")
                    return True
                except Exception as e:
                    logger.error(f"CalDAV connection failed: {e}")
                    # Fall through to simple credential check

            # Simple credential check as fallback
            if self.username and self.password:
                self.connected = True
                logger.info("Connection successful (basic)")
                return True
            logger.warning("Connection failed - missing credentials")
            logger.warning(f"Username: {self.username}, Password: {self.password}")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def create_reminder(self, reminder):
        """Create reminder in Apple Reminders and return the Apple ID"""
        try:
            logger.info(f"Creating Apple reminder for: {reminder.title}")
            
            if not self.connected:
                logger.info("Service not connected, attempting to connect...")
                if not self.connect():
                    logger.error("Failed to connect to Apple service")
                    return None

            # Try real CalDAV creation first if calendar is available
            if self._calendar is not None:
                try:
                    try:
                        from icalendar import Calendar, Event, Alarm  # type: ignore
                        icalendar_available = True
                    except Exception:
                        icalendar_available = False

                    # Build a VEVENT with an on-time alert
                    uid = f"{reminder.id}_{int(timezone.now().timestamp())}"
                    # Determine start/end datetimes from reminder_time (TimeField)
                    now_dt = timezone.localtime()
                    current_tz = timezone.get_current_timezone()
                    # Combine date with reminder_time (naive), then make it timezone-aware
                    naive_start = datetime.combine(now_dt.date(), reminder.reminder_time)
                    start_dt = timezone.make_aware(naive_start, current_tz)
                    if start_dt <= now_dt:
                        start_dt = start_dt + timedelta(days=1)
                    end_dt = start_dt + timedelta(minutes=5)
                    if icalendar_available:
                        cal = Calendar()
                        cal.add('PRODID', '-//DJANGO APP//EN')
                        cal.add('VERSION', '2.0')
                        event = Event()
                        event.add('UID', uid)
                        event.add('SUMMARY', reminder.title)
                        if getattr(reminder, 'description', None):
                            event.add('DESCRIPTION', reminder.description)
                        event.add('DTSTART', start_dt)
                        event.add('DTEND', end_dt)
                        # Add a display alarm at event time
                        try:
                            alarm = Alarm()
                            alarm.add('ACTION', 'DISPLAY')
                            alarm.add('DESCRIPTION', reminder.title)
                            alarm.add('TRIGGER', timedelta(minutes=0))
                            event.add_component(alarm)
                        except Exception:
                            pass
                        cal.add_component(event)
                        ics_data = cal.to_ical()
                    else:
                        # Plain ICS string fallback
                        start_s = start_dt.strftime('%Y%m%dT%H%M%S')
                        end_s = end_dt.strftime('%Y%m%dT%H%M%S')
                        description = (reminder.description or '').replace('\n', ' ').replace('\r', ' ')
                        ics_data = (
                            "BEGIN:VCALENDAR\r\n"
                            "VERSION:2.0\r\n"
                            "PRODID:-//DJANGO APP//EN\r\n"
                            "BEGIN:VEVENT\r\n"
                            f"UID:{uid}\r\n"
                            f"SUMMARY:{reminder.title}\r\n"
                            f"DTSTART:{start_s}\r\n"
                            f"DTEND:{end_s}\r\n"
                            f"DESCRIPTION:{description}\r\n"
                            "BEGIN:VALARM\r\n"
                            "ACTION:DISPLAY\r\n"
                            f"DESCRIPTION:{reminder.title}\r\n"
                            "TRIGGER:PT0M\r\n"
                            "END:VALARM\r\n"
                            "END:VEVENT\r\n"
                            "END:VCALENDAR\r\n"
                        ).encode('utf-8')

                    # Save the VEVENT to the calendar
                    saved = None
                    for method_name in ('add_event', 'save_event'):
                        method = getattr(self._calendar, method_name, None)
                        if callable(method):
                            try:
                                saved = method(ics_data)
                                logger.info(f"Saved VEVENT using {method_name}")
                                break
                            except Exception as e:
                                logger.warning(f"{method_name} failed: {e}")
                    if saved is None:
                        logger.error("No suitable method to save VEVENT on selected CalDAV collection")
                        return None

                    # Determine persistent identifiers from CalDAV response
                    # Prefer server resource href/url for the event id
                    apple_reminder_id = None
                    for attr in ('url', 'href', 'id', 'path'):
                        val = getattr(saved, attr, None)
                        if val:
                            apple_reminder_id = str(val)
                            break
                    if not apple_reminder_id and hasattr(saved, 'instance'):
                        try:
                            apple_reminder_id = str(getattr(saved.instance, 'url', '') or getattr(saved.instance, 'href', '')) or None
                        except Exception:
                            pass
                    if not apple_reminder_id:
                        # fallback to UID only if server URL not available
                        apple_reminder_id = uid

                    # Calendar identifier: try to persist the collection url
                    apple_calendar_id = None
                    for attr in ('url', 'href', 'id', 'path'):
                        val = getattr(self._calendar, attr, None)
                        if val:
                            apple_calendar_id = str(val)
                            break

                    # Update the reminder with Apple ID - IMPORTANT: Use update() to avoid recursive save
                    from ..models import Reminder
                    Reminder.objects.filter(id=reminder.id).update(
                        apple_reminder_id=apple_reminder_id,
                        apple_calendar_id=apple_calendar_id,
                        is_synced_with_apple=True,
                        last_sync_at=timezone.now()
                    )
                    logger.info(f"Updated database with Apple IDs: reminder={apple_reminder_id}, calendar={apple_calendar_id}")
                    return apple_reminder_id
                except Exception as e:
                    logger.error(f"Error creating VEVENT via CalDAV: {e}", exc_info=True)
                    # Fall through to test ID if CalDAV save failed

            # No valid CalDAV target: try webhook to Rappels via Shortcut if configured
            if getattr(self, 'webhook_url', None):
                try:
                    import requests  # type: ignore
                    payload = {
                        'title': reminder.title,
                        'notes': getattr(reminder, 'description', '') or '',
                        'due': str(getattr(reminder, 'reminder_time', '') or ''),
                    }
                    headers = {'Content-Type': 'application/json'}
                    if getattr(self, 'webhook_secret', None):
                        headers['X-Webhook-Secret'] = self.webhook_secret
                    resp = requests.post(self.webhook_url, json=payload, headers=headers, timeout=10)
                    if resp.ok:
                        resp_json = {}
                        try:
                            resp_json = resp.json()
                        except Exception:
                            resp_json = {}
                        apple_reminder_id = resp_json.get('id') or resp_json.get('url') or f"SHORTCUT_{reminder.id}_{int(timezone.now().timestamp())}"
                        from ..models import Reminder
                        Reminder.objects.filter(id=reminder.id).update(
                            apple_reminder_id=apple_reminder_id,
                            is_synced_with_apple=True,
                            last_sync_at=timezone.now()
                        )
                        logger.info(f"Created reminder via webhook; stored id: {apple_reminder_id}")
                        return apple_reminder_id
                    else:
                        logger.error(f"Webhook call failed with status {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.error(f"Webhook creation error: {e}", exc_info=True)

            logger.error("Aborting creation: no VTODO-capable collection and no webhook configured")
            return None
            
        except Exception as e:
            logger.error(f"Failed to create Apple reminder: {e}", exc_info=True)
            return None

def get_apple_reminders_service_for_user(user):
    """Get Apple Reminders service for a user"""
    try:
        logger.info(f"Getting Apple service for user: {user.username}")
        
        # Check if user has profile and Apple credentials
        if not hasattr(user, 'profile'):
            logger.warning(f"User {user.username} has no profile")
            return None
            
        profile = user.profile
        logger.info(
            f"Profile found: apple_connected={getattr(profile, 'is_apple_connected', 'NO ATTR')}, "
            f"username={getattr(profile, 'apple_username', 'NO ATTR')}"
        )
        
        # Ensure the profile actually has usable Apple credentials
        if hasattr(profile, 'has_apple_credentials') and profile.has_apple_credentials():
            # Decrypt password using the provided accessor
            apple_password = None
            if hasattr(profile, 'get_apple_password'):
                apple_password = profile.get_apple_password()
            
            logger.info(f"Decrypted password present: {'YES' if apple_password else 'NO'}")
            if not apple_password:
                logger.warning("Apple password missing after decryption; cannot initialize service")
                return None
            
            service = AppleRemindersService(
                profile.apple_username,
                apple_password,
                webhook_url=getattr(profile, 'reminders_webhook_url', None),
                webhook_secret=getattr(profile, 'reminders_webhook_secret', None),
            )
            logger.info("Apple service created successfully")
            return service
        else:
            logger.warning("User profile not properly configured for Apple (missing credentials)")
            
    except Exception as e:
        logger.error(f"Failed to get Apple service for user {user}: {e}", exc_info=True)
    
    return None