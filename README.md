# dev2cloud

Python client for the [Dev2Cloud](https://dev2.cloud) API — spin up ephemeral Postgres and Redis sandboxes in seconds.

## Installation

```bash
pip install dev2cloud
```

## Quick Start

Sign up at [dev2.cloud](https://dev2.cloud) and grab your API key from the [dashboard](https://dev2.cloud/dashboard).

### Create a Postgres sandbox

```python
from dev2cloud import Dev2Cloud, SandboxType

client = Dev2Cloud(api_key="d2c_...")

sandbox = client.create_sandbox(SandboxType.POSTGRES)

print(sandbox.url)
# postgresql://user:pass@connect.dev2.cloud:5432/postgres
```

### Create a Redis sandbox

```python
sandbox = client.create_sandbox(SandboxType.REDIS)

print(sandbox.url)
# redis://user:pass@connect.dev2.cloud:6379/0
```

### Manage sandboxes

```python
# List all active sandboxes
sandboxes = client.list_sandboxes()

# Get a sandbox by ID
sandbox = client.get_sandbox("sandbox-id")

# Delete a sandbox
client.delete_sandbox("sandbox-id")

# Delete all sandboxes
deleted_ids = client.delete_all()
```

### Async support

```python
from dev2cloud.asyncio import Dev2Cloud
from dev2cloud import SandboxType

client = Dev2Cloud(api_key="d2c_...")

sandbox = await client.create_sandbox(SandboxType.POSTGRES)
print(sandbox.url)
```

### Configuration

The API key can be provided directly or through the `D2C_API_KEY` environment variable:

```bash
export D2C_API_KEY="d2c_..."
```

```python
from dev2cloud import Dev2Cloud

client = Dev2Cloud()  # reads from D2C_API_KEY
```

## References

- [Homepage](https://dev2.cloud)
- [Dashboard](https://dev2.cloud/dashboard)
- [API Reference](https://api.dev2.cloud)
- [Usage Example](https://github.com/d2c-app/d2c-snippet)
- [X](https://x.com/dev2cloudmedia)

## License

MIT
