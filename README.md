# Shotclock web app

Basketball shot clock web app using Django with WebSocket support for real-time updates.

## Features

- Real-time shot clock display with WebSocket updates
- Control interface for starting/stopping the clock
- Multiple game sessions support
- RESTful API for clock state
- Server-sent events (SSE) for live streaming
- Responsive web interface

## Local development

This setup requires [uv](https://docs.astral.sh/uv/).

1. Create virtual environment and install packages

   ```bash
   uv sync
   ```

2. Set `DEBUG` option to `True` in `settings.py`

   This is required to serve the static files in local development server.

3. Run local server

   ```bash
   uv run uvicorn config.asgi:application --reload --port 8000
   ```
