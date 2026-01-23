import os
import ctypes
from ctypes import wintypes

if os.name == "nt":
    # Load kernel32.dll
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # Define GetUserDefaultLocaleName signature
    # int GetUserDefaultLocaleName(LPWSTR lpLocaleName, int cchLocaleName);
    kernel32.GetUserDefaultLocaleName.argtypes = [wintypes.LPWSTR, ctypes.c_int]
    kernel32.GetUserDefaultLocaleName.restype = ctypes.c_int

# Allocate buffer for locale name
LOCALE_NAME_MAX_LENGTH = 85  # per Windows docs


def user_default_locale() -> str:
    """
    Get user default locale encoded in BCP-47.
    """
    buffer = ctypes.create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)

    # Call the function
    result = kernel32.GetUserDefaultLocaleName(buffer, LOCALE_NAME_MAX_LENGTH)

    if result == 0:
        # Call failed
        error_code = ctypes.get_last_error()
        raise ctypes.WinError(error_code)

    return buffer.value


if __name__ == "__main__":
    print(user_default_locale())
