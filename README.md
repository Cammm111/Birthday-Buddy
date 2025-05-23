# Birthday Buddy

Birthday Buddy is a SaaS application that helps teams celebrate birthdays, with built-in Slack integration.

## Features

- Schedule and manage birthdays for team members
- Automatic birthday notifications via Slack
- Simple API for CRUD operations on users and birthdays

## Getting Started

### Prerequisites

- Python 3.12+
- pip (Python package installer)
- A [Slack API Token](https://api.slack.com/)

### Installation

1. **Clone the repository and enter the project folder:**
    ```sh
    git clone https://github.com/Cammm111/Birthday-Buddy.git
    cd Birthday-Buddy
    ```

2. **Set up your virtual environment:**
    ```sh
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On Mac/Linux:
    # source venv/bin/activate
    ```

3. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
    ```sh
    # Copy .env.example to .env (choose the command for your OS)
    copy .env.example .env        # Windows
    # cp .env.example .env        # Mac/Linux
    ```
    - Edit `.env` and add your Slack API token and other config values.

5. **Initialize the database:**
    - The app auto-creates `database.db` if needed.  
      *(If manual setup is required, add those commands here.)*

6. **Run the app:**
    ```sh
    python -m app.main
    ```

## Environment Variables

- `SLACK_API_TOKEN`: Your Slack bot token
- (Add other environment variables as needed)

## API Usage

Examples for common API endpoints (customize as your API grows):

- **Create a user**  
  `POST /users/`
- **Add a birthday**  
  `POST /birthdays/`
- **Get all birthdays**  
  `GET /birthdays/`

*(Add example payloads/responses as you define your API.)*

## Slack Integration

To enable Slack notifications:
- Invite your bot to your Slack workspace
- Ensure it has permissions like `chat:write`

## Contributing

Pull requests are welcome! For major changes, open an issue first to discuss what you’d like to change.

## License

