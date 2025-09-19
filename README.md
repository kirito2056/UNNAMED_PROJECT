# Personalized AI assistant

This project is a personalized, small Language Model (sLM) based AI assistant. It's designed to help with daily tasks, learning, and more, with a focus on voice and multimodal interactions.

## Project Overview

- **Core Function:** Voice-based AI assistant (schedule management, learning helper, music recommendation).
- **Inputs:** Voice (STT), Real-time Video, Device Sensors.
- **Outputs:** Streaming TTS, Text, JSON Action Blocks.
- **Architecture:** Modular, containerized services using FastAPI, Docker, and various AI/ML libraries.

## Getting Started

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd friend_like_ai
    ```

2.  **Setup environment variables:**
    Copy the `.env.example` file to `.env` and fill in the required values.

    ```bash
    cp .env.example .env
    ```

3.  **Build and run with Docker Compose:**

    ```bash
    docker-compose up --build
    ```

4.  **Check the application:**
    - API server: `http://localhost:8000`
    - API docs (Swagger UI): `http://localhost:8000/docs`
    - Health check: `http://localhost:8000/health`
