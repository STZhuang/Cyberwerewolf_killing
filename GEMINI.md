# Project Overview

This project is a real-time, multi-agent Werewolf game platform called "Cyber Werewolves". It allows human players to compete with and against AI-powered agents in a game of Werewolf. The platform is designed to be fair, with low latency and a complete game replay functionality.

**Key Technologies:**

*   **Frontend:** Vue.js with TypeScript, using the Arco Design UI library.
*   **Backend:** Python with FastAPI, responsible for the game logic, API, and WebSocket communication.
*   **AI Agents:** The agents are powered by Large Language Models (LLMs) and managed by the Agno framework.
*   **Database:** PostgreSQL is used for data storage, and Redis is used for caching.
*   **Infrastructure:** The entire application is containerized using Docker and managed with Docker Compose.

**Architecture:**

The application is composed of several services that work together:

*   **Web:** The Vue.js frontend that users interact with.
*   **API:** The FastAPI backend that handles game logic, user authentication, and communication with the database and other services.
*   **WebSocket Gateway:** A dedicated service for handling real-time communication between the clients and the backend.
*   **Agents:** A service that manages the AI agents, including their decision-making processes.
*   **Database:** A PostgreSQL database to store game data, user information, and other persistent data.
*   **Cache:** A Redis instance for caching frequently accessed data and managing transient game state.
*   **Message Queue:** NATS is used as a message queue for communication between services.
*   **Monitoring:** Prometheus and Grafana are used for monitoring the application's health and performance.

# Building and Running

The project uses Docker and Docker Compose for easy setup and deployment. The following commands are available in the `Makefile`:

*   `make setup`: Initializes the project by creating the `.env` file and pulling the necessary Docker images.
*   `make dev`: Starts the development environment.
*   `make build`: Builds the Docker containers for all services.
*   `make test`: Runs the tests for the backend and frontend.
*   `make clean`: Stops and removes all containers and volumes.
*   `make logs`: Shows the logs for all services.
*   `make shell service=<service_name>`: Opens a shell in the specified service's container.
*   `make db-reset`: Resets the database.

**To run the project in a development environment:**

1.  Make sure you have Docker and Docker Compose installed.
2.  Run `make setup` to initialize the environment.
3.  Run `make dev` to start all the services.
4.  The application will be available at `http://localhost:3000`.

# Development Conventions

*   **Code Style:** The project uses `black` and `isort` for Python code formatting and `prettier` for the frontend code.
*   **Linting:** `flake8` is used for linting the Python code and `eslint` for the frontend code.
*   **Testing:** `pytest` is used for backend testing and `vitest` for frontend testing.
*   **Modularity:** The backend is organized into routers for different functionalities, and the frontend uses a component-based architecture with a centralized store for state management.
*   **Infrastructure as Code:** The entire infrastructure is defined in the `docker-compose.yml` file, making it easy to replicate the environment.

# Project Structure

The project is organized into the following directories:

*   `apps/`: Contains the source code for the main applications:
    *   `api/`: The FastAPI backend.
    *   `agents/`: The AI agent service.
    *   `web/`: The Vue.js frontend.
    *   `websocket-gateway/`: The WebSocket gateway.
*   `packages/`: Contains shared packages for the Python and JavaScript code.
*   `infra/`: Contains infrastructure-related files, such as Docker configurations and deployment scripts.
*   `tests/`: Contains end-to-end and load tests.
*   `docs/`: Contains project documentation.

# API Endpoints

The FastAPI backend exposes the following main API endpoints:

*   `/auth/`: User authentication.
*   `/rooms/`: Room management (create, list, join, leave, start game).
*   `/admin/`: Admin-related functionalities.
*   `/llm-config/`: LLM configuration management.
*   `/game-actions/`: Game-related actions.

# WebSocket Events

The WebSocket gateway handles real-time communication using the following events:

*   `join_room`: When a user joins a room.
*   `leave_room`: When a user leaves a room.
*   `message`: When a user sends a message in a room.
*   `game_event`: For broadcasting game-related events to the clients.

# Agent Interaction

The AI agents interact with the game through a set of tools:

*   `say(text)`: To send a message in the game.
*   `vote(target_seat)`: To vote for a player.
*   `night_action(action, target_seat)`: To perform a night action (e.g., kill, check).
*   `ask_gm_for_clarification(question)`: To ask the Game Master for clarification on the rules.

Each agent is initialized with a set of instructions that define its role and objectives in the game. The agents use a language model to make decisions based on the current game state and their instructions.
