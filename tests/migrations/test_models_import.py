import importlib
import inspect
import pkgutil

import app.models
from app.core.db import Base


def test_all_models_imported():
    models_path = app.models.__path__
    modules = pkgutil.iter_modules(path=models_path)
    model_attributes = dir(app.models)

    misses = []
    for module in modules:
        module_file = importlib.import_module("app.models." + module.name)
        classes = inspect.getmembers(module_file, inspect.isclass)

        for name, cls in classes:
            if (
                issubclass(cls, Base)
                and cls is not Base
                and cls.__module__ == module_file.__name__
                and name not in model_attributes
            ):
                misses.append(name)

    assert len(misses) == 0, f"Missed model imports: {misses}"
