"""
Error messages for people using the site.

Rule: a user sees what went wrong in their own terms and what to do next.
They never see exception text, stack traces, SQL, file paths or service names.
Full details go to the server log, where developers can read them.

Usage inside an ``except`` block:

    from afridata.user_errors import log_exception, USER_MESSAGES

    except Exception:
        log_exception("profile update")          # full traceback to the log
        messages.error(request, USER_MESSAGES["profile_save"])
"""
import logging

logger = logging.getLogger("afridata.errors")

# Plain-language messages, keyed by what the user was doing.
USER_MESSAGES = {
    "generic": "Something went wrong on our side. Please try again in a moment.",
    "profile_save": "We couldn't save your profile changes. Please check the form and try again.",
    "dataset_action": "We couldn't complete that action on the dataset. Please try again.",
    "bulk_action": "The bulk action couldn't be completed. Some items may not have changed. Please try again.",
    "token_adjust": "We couldn't adjust the token balance. Please try again.",
    "moderation": "We couldn't apply that moderation action. Please try again.",
    "setting_save": "We couldn't save that setting. Please try again.",
    "topic_create": "We couldn't create the topic. Please try again.",
    "delete": "We couldn't delete that. Please try again.",
    "rate_limits": "We couldn't update the rate limits. Please try again.",
    "report_generate": "We couldn't generate the report. Please try again.",
    "notification_create": "We couldn't create the notification. Please try again.",
    "email_campaign": "Some emails couldn't be sent. Please check the campaign and try again.",
    "metadata_start": "We couldn't start the metadata analysis. Please try again in a few minutes.",
    "file_read": "We couldn't read this file, so its preview and chart aren't available. "
                  "The file may be damaged or in an unexpected format.",
    "payment_service": "We couldn't reach the payment service right now. Please try again shortly.",
    "standardization": "Standardization couldn't be completed. Please try again, or contact support if it keeps happening.",
    "standardization_prepare": "We couldn't prepare this dataset for standardization. Please try again.",
    "standardization_save": "We couldn't save your edits. Please try again.",
    "download_prepare": "We couldn't prepare the download. Please try again.",
    "job_status": "We couldn't check the job status right now. Please try again.",
}


def log_exception(context: str) -> None:
    """Record the current exception with its full traceback. Call only inside an ``except`` block."""
    logger.exception("Failed: %s", context)
