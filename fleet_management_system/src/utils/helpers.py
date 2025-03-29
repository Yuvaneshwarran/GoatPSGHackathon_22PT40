import os
import time
import logging

def setup_logging(log_file):
    """
    Set up logging to a file.
    
    Args:
        log_file (str): Path to the log file.
    """
    # Create the directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
def log_event(event_type, details):
    """
    Log an event.
    
    Args:
        event_type (str): Type of the event.
        details (dict): Details of the event.
    """
    logging.info(f"{event_type}: {details}")
    
def get_timestamp():
    """
    Get a formatted timestamp.
    
    Returns:
        str: Formatted timestamp.
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 