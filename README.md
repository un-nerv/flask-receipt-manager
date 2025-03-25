# This is Most powerfull Receipt manager powered by AI

# Install guide
1. Create .env
2. Go to https://aistudio.google.com/ and get API key
3. Enter your key to .env file
```
GEMINI_API_KEY=Enter_Your_API_KEY_HERE
```
4. Install Docker

    You can use Docker official script on Ubuntu
```
#On Ubuntu
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $(whoami)
exit
```

5. Run the command below to start server

    ```
    docker compose up --build
    ```
7. Go to http://localhost:5001

### Features will be supported
- Geocoding store location and send to [Dawarich](https://github.com/Freika/dawarich)
