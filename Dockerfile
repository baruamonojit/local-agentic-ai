# Use an official Python runtime with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project specification files first for efficient caching
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv without installing the root project package yet
RUN uv sync --frozen --no-install-project --no-dev

# Copy application files
COPY . .

# Expose default Streamlit port
EXPOSE 8501

# Configure Streamlit to run headlessly inside Docker
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Launch Streamlit using uv run
CMD ["uv", "run", "streamlit", "run", "app.py"]