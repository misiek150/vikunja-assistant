---
name: python-dev
description: Guidelines for writing and refactoring modern Python code using OOP, strong typing, and robust architecture.
---

# GitHub Copilot Instructions: Python Modern OOP Guidelines

You are an expert Python software engineer specializing in clean, modern Object-Oriented Programming (OOP), strong domain modeling, and robust software architecture. 

When generating or refactoring Python code, adhere strictly to the following standards.

---

## 1. Core Principles

- **Target Python Version:** Python 3.10+ (use modern syntax like `X | Y` for unions, `match/case`, `Self`, `@override`).
- **Composition over Inheritance:** Prefer composition and interface implementation over multi-level inheritance hierarchies. Keep inheritance depth $\le 2$.
- **SOLID Principles:**
  - **Single Responsibility (SRP):** Classes should have one reason to change. Separate data structures from business logic and I/O.
  - **Open/Closed (OCP):** Use abstractions (`ABC`) so behavior can be extended without modifying existing code.
  - **Liskov Substitution (LSP):** Subtypes must strictly satisfy parent interfaces and contracts. Use `typing.override`.
  - **Interface Segregation (ISP):** Prefer small, single-purpose interfaces over bloated contracts.
  - **Dependency Inversion (DIP):** Depend on abstractions (`ABC`), inject dependencies via `__init__` and wire them in the IoC container.

---

## 2. Interface & Class Design

### Data Holders vs. Behavioral Classes
- **Data Containers:** Use `@dataclass(slots=True, frozen=True)` for immutable value objects or domain entities. Use `Pydantic v2` (`BaseModel`) for schemas requiring input validation or dynamic serialization.
- **Service/Logic Classes:** Use standard classes with explicit dependency injection. Do not store transient state inside service classes unless necessary.

### Abstractions: ABC + Implementations
- **Default:** every service/integration is defined as an abstract class (`abc.ABC` with `@abstractmethod`) and one or more concrete implementations that subclass it (use `@override`). Consumers depend only on the abstract class.
- **Naming:** abstract class `Foo`, implementation `HttpFoo` / `InMemoryFoo`, etc. Keep abstract classes small and single-purpose (ISP).
- `typing.Protocol` is acceptable only for third-party types we cannot subclass.

```python
from abc import ABC, abstractmethod
from typing import override

class Repository(ABC):
    @abstractmethod
    def get_by_id(self, item_id: str) -> DomainEntity | None: ...

    @abstractmethod
    def save(self, entity: DomainEntity) -> None: ...

class HttpRepository(Repository):
    @override
    def get_by_id(self, item_id: str) -> DomainEntity | None: ...

    @override
    def save(self, entity: DomainEntity) -> None: ...
```

---

## 3. Type Safety & Encapsulation

* **Strict Type Annotations:** Annotate all function parameters, return values, and class variables.
* **Encapsulation:**
* Mark private/internal methods and attributes with a leading single underscore (`_attribute`).
* Use `@property` for dynamic getters or validation. Avoid standard getter/setter boilerplate (`get_x()`, `set_x()`) unless enforcing complex domain invariants.


* **Immutability:** Default to immutable data structures where possible.

---

## 4. Error Handling & Domain Exceptions

* Define custom domain exception hierarchies inheriting from a base `DomainError` (derived from `Exception`).
* Fail fast and handle errors at boundary layers, not deep within core domain logic.

```python
class DomainError(Exception):
    """Base exception for domain errors."""

class EntityNotFoundError(DomainError):
    def __init__(self, entity_id: str) -> None:
        super().__init__(f"Entity with ID '{entity_id}' was not found.")

```

---

## 5. Canonical Class Template

When creating new modules, structure classes using this layout:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import override
import uuid

# 1. Custom Exceptions
class OrderError(Exception):
    """Base exception for order processing."""

# 2. Value Objects / Entities (Dataclasses / Pydantic)
@dataclass(slots=True, frozen=True)
class OrderItem:
    product_id: str
    unit_price: float
    quantity: int

    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity

# 3. Abstractions (ABC)
class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> bool: ...

# 4. Service Classes (Dependency Injection & Single Responsibility)
class OrderService:
    def __init__(self, payment_processor: PaymentProcessor) -> None:
        self._payment_processor = payment_processor

    def checkout(self, items: list[OrderItem]) -> str:
        if not items:
            raise OrderError("Cannot checkout an empty list of items.")

        total_amount = sum(item.total_price for item in items)
        
        success = self._payment_processor.process_payment(total_amount)
        if not success:
            raise OrderError("Payment processing failed.")

        return str(uuid.uuid4())

```

---

## 6. IoC Container (dependency-injector)

* Use `dependency-injector` (`DeclarativeContainer`) as the single composition root, e.g. `container.py`. Only the container instantiates implementations.
* Classes receive abstractions through `__init__`; do not use `@inject`/`Provide[...]` inside domain or service classes.
* Register providers: `providers.Singleton` for stateless/shared services, `providers.Factory` for per-use objects, `providers.Configuration` for env-based settings (e.g. Vikunja URL and token).
* Every new abstract class + implementation must be registered in the container.
* Do not use service locators or global container access from core logic; resolve only at the application entry point.

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    repository = providers.Singleton(HttpRepository, base_url=config.base_url)
    service = providers.Factory(OrderService, repository=repository)
```

---

## 7. Logging (Seq)

* Logs are shipped to Seq. Use the stdlib `logging` module in code and `seqlog` as the Seq handler; configure it once at the application entry point / composition root, never inside domain or service classes.
* Seq URL and API key come from configuration (`<SEQ_URL>`, `<SEQ_API_KEY>` env vars); never hardcode or log secrets.
* Get loggers with `logging.getLogger(__name__)` and inject them via `__init__` where a class logs (or register them in the container), so tests can pass a mock or use `caplog`.
* Use structured logging: named message-template properties rather than f-strings, so Seq can index and query them.
* Never log tokens, passwords, or full request bodies. Log exceptions with `logger.exception(...)` or `exc_info=True` at boundary layers.
* Include correlation context (e.g. task or project IDs) as properties.

```python
import logging
import seqlog

def configure_logging(seq_url: str, api_key: str | None) -> None:
    seqlog.log_to_seq(
        server_url=seq_url,
        api_key=api_key,
        level=logging.INFO,
        batch_size=10,
        auto_flush_timeout=2,
        override_root_logger=True,
    )

class TaskService:
    def __init__(self, repository: Repository, logger: logging.Logger) -> None:
        self._repository = repository
        self._logger = logger

    def complete(self, task_id: int) -> None:
        self._logger.info("Completing task {task_id}", task_id=task_id)
```

* Keyword-argument templates (`logger.info("... {x}", x=1)`) only work on loggers created after `seqlog` is configured; create loggers after `configure_logging` runs. Verify this against the installed `seqlog` version.
* Logging configuration is wired in the container (e.g. a `providers.Resource` that calls `configure_logging`), and tests must not send logs to Seq.

---

## 8. Testing & Decoupling

* Avoid global mutable state, singleton patterns, or direct instantiation of external services inside core logic classes.
* Unit tests use `pytest`. Prefer unit-testing a class by passing fakes or `MagicMock(spec=AbstractClass)` directly to its constructor. For container-level tests, use `container.<provider>.override(providers.Object(fake))` or `with container.override_providers(...)`.
* **New implementation rule:** every new implementation (class, function module) must be created together with its unit tests in the same change, mirroring the source layout under `tests/`. Cover success paths, edge cases, and error paths.
* **Change rule:** every change to an existing implementation requires reviewing and updating its unit tests (add tests for new behavior, fix tests for changed behavior, remove obsolete ones).
* **Validation rule:** after any implementation or test change, run the relevant tests (and the full suite if shared code changed). A task is not complete until they pass; report the result and fix failures rather than skipping or deleting tests.

