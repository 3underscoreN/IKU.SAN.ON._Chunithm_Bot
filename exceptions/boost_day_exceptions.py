from discord.app_commands import AppCommandError

class BaseBoostDayError(AppCommandError):
    """Base exception for Boost Day related errors."""
    pass

class BoostDayError(BaseBoostDayError):
    """Generic Boost Day error."""
    
    details: str = "An error occurred"
    message: str = "發生錯誤。"
    user_error: bool = True

    def __init__(self, *, user_error: bool | None = None, details: str | None = None, message: str | None = None):
        payload = {
            "user_error": user_error if user_error is not None else self.user_error,
            "details": details or self.details,
            "message": message or self.message,
        }
        super().__init__(payload)

class InvalidDateFormatException(BoostDayError):
    details = "Invalid date format"
    message = "日期格式無效。請使用 YYYY-MM-DD。"

class DateInPastException(BoostDayError):
    details = "Date is in the past"
    message = "該日已經過去。請提出一個未來的日期。"

class InvalidMonthFormatException(BoostDayError):
    details = "Invalid month format"
    message = "月份格式無效。請使用 YYYY-MM。"

class MonthOutOfRangeException(BoostDayError):
    details = "Month out of range"
    message = "請提出本月或下月的加成日。"

class RegistrationClosedException(BoostDayError):
    details = "Registration closed for current month"
    message = "本月的加成日提案已在截止日後關閉。請提出下月的加成日。"

class NoProposalsFoundException(BoostDayError):
    details = "No proposals found"
    message = "在指定的月份中未找到任何加成日提案。"

class ProposalNotFoundException(BoostDayError):
    details = "Proposal not found"
    message = "未找到指定的加成日提案。"

class DuplicateProposalException(BoostDayError):
    details = "Duplicate proposal"
    message = "您已經為該日期提出過加成日提案，無法重複提案相同日期。"