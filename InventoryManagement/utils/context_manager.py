import threading
from contextlib import contextmanager

_thread_locals = threading.local()


@contextmanager
def set_current_context(user, **kwargs):
    """
    Context manager to set the current user and additional context in thread-local storage.
    """
    try:
        _thread_locals.user = user
        _thread_locals.context = kwargs  # Store additional context as a dictionary
        yield
    finally:
        # Clear the thread-local storage after the context is exited
        _thread_locals.user = None
        _thread_locals.context = None

def get_current_user():
    """
    Retrieve the current user from thread-local storage.
    """
    return getattr(_thread_locals, "user", None)

def get_current_context():
    """
    Retrieve the additional context from thread-local storage.
    """
    return getattr(_thread_locals, "context", {})