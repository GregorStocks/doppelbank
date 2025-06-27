# General Coding Standards

This document outlines general coding standards for the project. Adhering to these standards ensures consistency, readability, and maintainability across the codebase.

## Dataclasses

For data structures that primarily hold data (e.g., parsed IDs, API request/response bodies, configuration objects), prefer using Python's `dataclasses` module. Dataclasses provide a concise way to define classes that are primarily used for storing data, offering benefits like automatic `__init__`, `__repr__`, `__eq__`, and `__hash__` methods.

**Guideline:** Use dataclasses for any new data-holding structures unless there's a compelling reason to use a different approach (e.g., a class with complex behavior, a Pydantic model for validation).

## Other Standards

(To be expanded with more general coding standards as needed.)
