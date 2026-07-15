import logging
import pytest
from backend.security_decorators import no_log_zone, no_log_zone_async

def test_no_log_zone_suppresses_logs(caplog):
    caplog.set_level(logging.DEBUG)
    
    @no_log_zone
    def sensitive_operation():
        logging.getLogger().info("This is a sensitive log that should not appear")
        logging.getLogger().error("This is an error log that should not appear")
        return "success"
        
    result = sensitive_operation()
    assert result == "success"
    
    # Caplog should not have captured these logs because they were suppressed
    assert "This is a sensitive log that should not appear" not in caplog.text

@pytest.mark.asyncio
async def test_no_log_zone_async_suppresses_logs(caplog):
    caplog.set_level(logging.DEBUG)
    
    @no_log_zone_async
    async def sensitive_operation_async():
        logging.getLogger().info("This is an async sensitive log that should not appear")
        return "success_async"
        
    result = await sensitive_operation_async()
    assert result == "success_async"
    
    # Caplog should not have captured these logs because they were suppressed
    assert "This is an async sensitive log that should not appear" not in caplog.text
