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

* Spotify\*
* Yandex.Music
* Last.fm
* Apple Music

### Downloading tracks from:

* Deezer
* Soundcloud
* Youtube

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/es3n1n/nowplaying.git
   cd nowplaying
   ```

2. Install Poetry:
   ```bash
   python3 -m pip install poetry==1.8.1
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

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

## Local Development

1. Activate the virtual environment:
   ```bash
   poetry shell
   ```

2. Run the bot:
   ```bash
   python3 main.py
   ```
   or
   ```bash
   python3 -m nowplaying
   ```

## Testing

Run the test suite using pytest:

```bash
pytest .
```

## Linting

This project uses a few linters

1. Flake8
   ```bash
   poetry run flake8 .
   ```
2. Mypy
   ```bash
   poetry run mypy .
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the Apache 2 License - see the [LICENSE](LICENSE) file for details.

---

\* Some features may be limited for Spotify due to the application not being approved *(yet)*.

![spotify being spotify](https://i.imgur.com/xfPfiP1.png)
