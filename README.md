# Most powerfull selfhostable Receipt manager powered by AI
⚠️This manager app is under development!!!

 Use at your own risk!!!

### Key features
- Input data from image files
- delete/insert data manualy

# Install guide
1. Clone this repo
2. Create .env
3. Go to https://aistudio.google.com/ and get API key
4. Enter your key to .env file
    ```
    GEMINI_API_KEY=Enter_Your_API_KEY_HERE
    ```
5. Install Docker

    You can use Docker official script on Ubuntu
    ```
    #On Ubuntu
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker $(whoami)
    exit
    ```

6. Run the command below to start server

    ```
    docker compose up --build
    ```
7. Go to http://localhost:5001

# Features to be supported
- Geocoding store location and send to [Dawarich](https://github.com/Freika/dawarich)
- Mobile app (It would be PWA)
- Support for local AI
