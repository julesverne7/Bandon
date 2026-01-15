from typing import Dict, Optional


def choices(klass):    
    """Returns TextChoices classes' items in an array for Django to process. Used while creating new choice fields,
    and fed into 'choices=' argument.\n 
    Example code:`status = models.CharField(max_length=50, choices=choices(PropertyStatusType))`"""
    return [(v, v.capitalize()) for k, v in vars(klass).items() if isinstance(v, str) and not k.startswith("__")]


def named_choices(klass, mapping: Optional[Dict[str, str]] = None):
    mapping = mapping or {}
    return [{"name": mapping.get(v, v.capitalize()), "value": v} for k, v in vars(klass).items() if isinstance(v, str) and not k.startswith("__")]


def class_strings(klass):
    return [v for k, v in vars(klass).items() if isinstance(v, str) and not k.startswith("__")]


class FileStatus:
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    FAILED = 'Failed' 