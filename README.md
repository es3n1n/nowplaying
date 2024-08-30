# playinnowbot

<p align="center">
  <img src="https://i.imgur.com/pmBfFF0.png" alt="preview">
</p>

A Telegram bot for sharing and discovering music across various platforms.

[Try the hosted version of this bot](https://t.me/playinnowbot)

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Local Development](#local-development)
- [Testing](#testing)
- [Linting](#linting)
- [Contributing](#contributing)
- [License](#license)

## Features

### Supported platforms:

* Spotify
* Yandex.Music
* Last.fm
* Apple Music

### Tracks downloading:

For track downloading, this bot uses a custom tool called µdownloader, 
which downloads tracks **exclusively from YouTube** using song.link. 

Due to legal reasons, I do not plan to open-source µdownloader anytime soon. 
Therefore, if you want to host your own version of this bot, 
you will need to implement your own track downloading algorithm.

## Configuration

Copy the example environment file and edit it with your settings:

```
cp .env.example .env
```

Edit the `.env` file with your preferred text editor and add the necessary API keys and configurations.

## Deployment

To deploy using Docker:

```bash
docker compose up -d --build
```

## Local installation

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Windows:
   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## Local Development

To run the bot use the following command:
```bash
uv run python3 -m nowplaybot
```

## Testing

Run the test suite using pytest:

```bash
pytest .
```

## Linting

This project uses a few linters

1. Ruff
   ```bash
   ruff format; ruff check --fix
   ```

2. Mypy
   ```bash
   mypy nowplaying
   ```

## Stored data about your account

This bot stores minimal information about you and your authorized platforms. It only retains data necessary for its proper functionality.

When you authorize on a platform, the bot creates a database entry with your Telegram ID and an authorization token, which is later used for communications with that platform (mainly for requesting recently played tracks). This data is never used for downloading or other purposes.

If an unexpected error occurs, the bot may send serialized data about the event to the developer, which could include your Telegram account information (ID, name, etc.).

When you request a track that isn't cached, the bot will attempt to download it from YouTube (if possible) and "cache" it by sending it to a specific private Telegram channel. The caption for this track will include your Telegram ID, name, and username.

If you wish to remove all information about your account, feel free to contact me, and I will delete the logs. For cached tracks, I will edit the captions, but the cached tracks will remain available. If you want to remove your stored platform token, please use the `/logout` command instead.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the Apache 2 License - see the [LICENSE](LICENSE) file for details.
