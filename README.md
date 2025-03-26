# Most powerful self-hosted Receipt Manager powered by AI
⚠️This manager app is under development!!!

Use at your own risk!!!

### Key features
- Input data from image files
- Delete/insert data manually
- get data from google maps
- Send store location to [Dawarich](https://github.com/Freika/dawarich)

# Install guide
1. Clone this repo
2. Create .env
3. Go to https://aistudio.google.com/ and obtain an API key
4. Enter your key into the .env file:
    ```
    GEMINI_API_KEY=Enter_Your_API_KEY_HERE
    ```
5. Install Docker

    You can use Docker's official script on Ubuntu:
    ```
    # On Ubuntu
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker $(whoami)
    exit
    ```

6. Run the command below to start the server:
    ```
    docker compose up --build
    ```
7. Go to http://localhost:5001

# Planned Features
- Mobile app (It would be PWA)
- Support for local AI
