from functools import wraps
import time


def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_attempts - 1:
                        print("Retries failed, cannot respond currently.")
                        raise e
                    print(f"Retrying, attempt {i + 1} out of {max_attempts}")
                    time.sleep(delay)

        return wrapper

    return decorator
