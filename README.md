# PTPED AQUA

Microservice project that exposes endpoints for accessing and processing data from AQUA using CSV files

## Features

- **Basic Authentication**: Secure access to the API endpoints.
- **Data Sanitization**: NaN or infinity values are replaced with `None`.
- **API Endpoints**:
  - `GET /visual_id`: Returns all visual_id records.
  - `GET /visual_id/:visual_id`: Retrieves records for a specific visual_id.
  - `GET /visual_id/:visual_id/qdf`: Extracts and returns specific QDF values from columns containing `~`.
  - `GET /visual_id/:visual_id}/qdf/:qdf`: Retrieves specific values from columns by QDF matching.

## Installation

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized deployment)

### Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/memelogit/ptped-aqua.git
    cd your-project-directory
    ```

2. Install dependencies:

    Using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

    Or, use Docker (if you prefer containerized setup):

    ```bash
    docker build -t aqua .
    ```

### Environment Variables

Create a `.env` file in the root directory with the following content:

```txt
ENV_USERNAME=your-username
ENV_PASSWORD=your-password
```

### Running the Application

To start the application locally on the 3000 port with 10 workers:

```bash
uvicorn main:app --host 0.0.0.0 --port 3000 --workers 10 --reload
```

Alternatively, if you're using Docker:
```bash
docker run -p 3000:3000 aqua
```