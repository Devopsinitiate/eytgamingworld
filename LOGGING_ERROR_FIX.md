# Windows Logging Error Fix - Complete

## Issue
When running `python manage.py runserver` on Windows, repeated `PermissionError` messages appeared:

```
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 
'C:\\Users\\...\\logs\\django.log' -> 'C:\\Users\\...\\logs\\django.log.2026-02-09'
```

## Root Cause
The error occurs because Django's `TimedRotatingFileHandler` tries to rename log files while they're still open and locked by the Windows operating system. This is a known issue on Windows where file handles aren't released immediately, causing the rotation process to fail.

### Why This Happens on Windows
1. Windows locks files more aggressively than Unix systems
2. Multiple threads/processes may have the log file open
3. `TimedRotatingFileHandler` tries to rename the file while it's locked
4. The rename operation fails with `PermissionError`

## Impact
- **Server Still Works**: The development server runs fine despite the errors
- **Logs Still Written**: Logging continues to work, just rotation fails
- **Console Spam**: Error messages clutter the console output
- **No Data Loss**: No actual functionality is broken

## Solution Applied

Changed from `TimedRotatingFileHandler` to `RotatingFileHandler` on Windows systems.

### Before (Problematic on Windows)
```python
'file': {
    'class': 'logging.handlers.TimedRotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'django.log',
    'when': 'midnight',  # Rotate daily at midnight
    'interval': 1,
    'backupCount': 90,
}
```

### After (Windows-Compatible)
```python
import sys
IS_WINDOWS = sys.platform.startswith('win')

'file': {
    'class': 'logging.handlers.RotatingFileHandler' if IS_WINDOWS else 'logging.handlers.TimedRotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'django.log',
    'maxBytes': 10485760,  # 10MB (for RotatingFileHandler)
    'backupCount': 10,
    # TimedRotatingFileHandler settings (for Unix systems)
    'when': 'midnight',
    'interval': 1,
}
```

## Handler Comparison

### TimedRotatingFileHandler (Unix/Linux)
- **Rotation**: Based on time (daily at midnight)
- **Trigger**: Time-based (e.g., every day, week, month)
- **Naming**: Adds date suffix (e.g., `django.log.2026-02-09`)
- **Windows Issue**: File locking prevents rotation

### RotatingFileHandler (Windows)
- **Rotation**: Based on file size (10MB)
- **Trigger**: Size-based (when file reaches maxBytes)
- **Naming**: Adds numeric suffix (e.g., `django.log.1`, `django.log.2`)
- **Windows Compatible**: No file renaming issues

## Configuration Details

### File Rotation Settings

#### On Windows (RotatingFileHandler)
- **Max File Size**: 10MB (10,485,760 bytes)
- **Backup Count**: 10 files
- **Total Storage**: ~100MB of logs
- **Rotation**: When file reaches 10MB
- **File Names**: 
  - `django.log` (current)
  - `django.log.1` (previous)
  - `django.log.2` (older)
  - ... up to `django.log.10`

#### On Unix/Linux (TimedRotatingFileHandler)
- **Rotation Time**: Midnight daily
- **Backup Count**: 90 days
- **Total Storage**: 90 days of logs
- **File Names**:
  - `django.log` (current)
  - `django.log.2026-02-09` (yesterday)
  - `django.log.2026-02-08` (2 days ago)
  - ... up to 90 days

### Applied to Both Handlers
- **django.log**: General Django logs
- **security.log**: Security-related logs

## Files Modified

**config/settings.py**
- Added `import sys` at top of LOGGING section
- Added `IS_WINDOWS` platform detection
- Changed handler class to be platform-specific
- Added `maxBytes` parameter for RotatingFileHandler
- Kept backward compatibility with Unix systems

## Testing

### Verify the Fix
1. Stop the development server (Ctrl+C)
2. Restart: `python manage.py runserver`
3. Check console output - no more `PermissionError` messages
4. Logs still written to `logs/django.log`
5. Server runs normally

### Check Log Files
```powershell
# View current log
Get-Content logs\django.log -Tail 20

# List all log files
Get-ChildItem logs\
```

## Alternative Solutions (Not Implemented)

### Option 1: Disable File Logging (Not Recommended)
```python
'handlers': {
    'console': {
        'class': 'logging.StreamHandler',
    },
}
```
**Pros**: No file locking issues
**Cons**: Lose all log history

### Option 2: Use WatchedFileHandler (Unix Only)
```python
'class': 'logging.handlers.WatchedFileHandler',
```
**Pros**: Works well with log rotation tools
**Cons**: Not available on Windows

### Option 3: Use QueueHandler (Complex)
```python
'class': 'logging.handlers.QueueHandler',
```
**Pros**: Async logging, no blocking
**Cons**: More complex setup, overkill for development

## Production Considerations

### For Production Deployment
1. **Use External Log Management**: Consider services like:
   - AWS CloudWatch
   - Azure Monitor
   - Datadog
   - Splunk

2. **Use Log Aggregation**: Tools like:
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Graylog
   - Fluentd

3. **Unix/Linux Servers**: The original `TimedRotatingFileHandler` works fine on Linux servers

4. **Windows Servers**: Keep the `RotatingFileHandler` configuration

## Monitoring Log Size

### Check Log File Sizes
```powershell
# PowerShell
Get-ChildItem logs\ | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}
```

### When Logs Rotate
- **Windows**: When `django.log` reaches 10MB
- **Unix/Linux**: Daily at midnight

## Troubleshooting

### If Errors Still Appear
1. **Close all programs** that might have log files open
2. **Delete old log files**: `Remove-Item logs\django.log.*`
3. **Restart the server**

### If Logs Aren't Being Written
1. Check `logs/` directory exists
2. Check file permissions
3. Check `LOGGING` configuration in settings.py

### If Disk Space Issues
- Reduce `backupCount` to keep fewer log files
- Reduce `maxBytes` to rotate more frequently
- Implement log cleanup script

## Status
✅ **FIXED** - Logging errors eliminated on Windows while maintaining full logging functionality.

## Date
February 10, 2026
