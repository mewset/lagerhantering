class InventoryError(Exception):
    """Base exception for inventory-related errors"""
    pass


class InventoryItemNotFoundError(InventoryError):
    """Raised when an inventory item cannot be found"""
    def __init__(self, item_id: int):
        self.item_id = item_id
        super().__init__(f"Inventory item with ID {item_id} not found")


class InventoryDataError(InventoryError):
    """Raised when there's an issue with inventory data integrity"""
    pass


class FileOperationError(InventoryError):
    """Raised when file operations fail"""
    def __init__(self, operation: str, file_path: str, original_error: Exception = None):
        self.operation = operation
        self.file_path = file_path
        self.original_error = original_error
        message = f"Failed to {operation} file {file_path}"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)


class ValidationError(InventoryError):
    """Raised when input validation fails"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for {field}: {message}")


class ConfigurationError(InventoryError):
    """Raised when there's a configuration issue"""
    pass


class BackupError(InventoryError):
    """Raised when backup operations fail"""
    def __init__(self, operation: str, details: str = None):
        self.operation = operation
        message = f"Backup operation failed: {operation}"
        if details:
            message += f" - {details}"
        super().__init__(message)


class UpdaterError(InventoryError):
    """Raised when updater operations fail"""
    def __init__(self, operation: str, details: str = None):
        self.operation = operation
        message = f"Updater operation failed: {operation}"
        if details:
            message += f" - {details}"
        super().__init__(message)


class ProcessManagementError(UpdaterError):
    """Raised when process management operations fail"""
    def __init__(self, pid: int, operation: str, details: str = None):
        self.pid = pid
        message = f"Process {pid} {operation} failed"
        if details:
            message += f": {details}"
        super().__init__(operation, message)


class GitOperationError(UpdaterError):
    """Raised when Git operations fail"""
    def __init__(self, command: str, details: str = None):
        self.command = command
        message = f"Git command '{command}' failed"
        if details:
            message += f": {details}"
        super().__init__(f"git {command}", message)