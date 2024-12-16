# Email Unsubscriber

**Email Unsubscriber** is a command-line tool that helps users manage their email inbox by fetching emails, displaying unsubscribe links, and allowing users to unsubscribe from mailing lists easily. It supports **Gmail** and **Yahoo Mail** accounts and provides interactive options to handle emails effectively.

## Features

- Fetches emails and displays unsubscribe links.
- Allows users to unsubscribe directly from mailing lists.
- Keeps track of emails that have been unsubscribed (`history.json`) and those explicitly skipped (`skipped.json`).
- Ensures duplicates are removed and maintains unique entries per session.
- Progress bar for tracking email fetch progress.
- Supports multiple email accounts, keeping `history` and `skipped` separate for each account.
- Configurable number of emails to fetch in each session.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/email-unsubscriber.git
   cd email-unsubscriber
   ```

2. Create a virtual environment and install dependencies using `make`:
   ```bash
   make install
   ```

3. You're ready to run the application!

---

## Usage

### Basic Command

Run the tool using the `make run` command. Provide your email, password, and the number of emails to fetch:

```bash
make run email={your_email} password={your_password} items={number_of_emails_to_fetch}
```

Example:
```bash
make run email=your_email@gmail.com password=yourpassword items=50
```

### Interactive Options

After fetching emails, the tool will display a table of emails with unsubscribe links. You can:

- **View Emails:** Browse emails interactively in a table format.
- **Open Unsubscribe Links:** Select an email index (e.g., `2`) to open all unsubscribe links for that email in your default browser.
- **Mark as Done:** Use `index-done` (e.g., `2-done`) to mark an email as unsubscribed and add it to the `history.json`.
- **Skip Emails:** Use `index-skip` (e.g., `2-skip`) to mark an email as skipped and add it to the `skipped.json`. Skipped emails will not appear in future sessions.
- **Exit:** Type `exit` to quit the application.

---

## How It Works

### Skipping and History

- **History (`history.txt`):** Tracks emails you’ve already unsubscribed from (with a valid unsubscribe link). This works only for the email address from the application runtime.
- **Skipped Emails (`skipped.json`):** Tracks emails you choose to skip explicitly. These will not appear in future sessions. These are available throughout any email address added at runtime.

### Fetching More Emails

- If duplicates or skipped emails reduce the total number of unique fetched items, the tool will automatically fetch additional emails until the specified number (`items`) is reached.

### Example Output Table

```
Emails with Unsubscribe Links (4/10)
┏━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Index ┃ Sender                      ┃ Email                        ┃ Unsubscribe Links           ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃   0   │ Amazon Web Services         │ aws-marketing-email-replies… │ https://email.awscloud.com  ┃
┃   1   │ GitHub                      │ noreply@github.com           │ No links found              ┃
┃   2   │ Google                      │ no-reply@accounts.google.com │ No links found              ┃
┃   3   │ Temu                        │ temu@eu.temuemail.com        │ https://www.temu.com/unsub… ┃
┗━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Project Structure

```
email-unsubscriber/
├── email_unsubscribe.py   # Main script
├── requirements.txt       # Python dependencies
├── history.txt            # Tracks unsubscribed emails (generated dynamically)
├── skipped.json           # Tracks skipped emails (generated dynamically)
├── README.md              # Project documentation
├── Makefile               # Automation commands
└── venv_email_unsubscribe # Virtual environment (ignored by `.gitignore`)
```

---

## Makefile Commands

- **Install:**
  Creates a virtual environment, installs dependencies, and prepares the tool for use:
  ```bash
  make install
  ```

- **Run:**
  Launches the tool. Provide your email, password, and the number of emails to fetch:
  ```bash
  make run email={email} password={password} items={number_of_emails_to_fetch}
  ```

- **Clean:**
  Removes the virtual environment and temporary files:
  ```bash
  make clean
  ```

- **All:**
  Cleans, installs:
  ```bash
  make all 
  ```

---

## Requirements

- Python 3.8 or higher
- IMAP email account (Gmail, Yahoo)
- Dependencies (installed via `make install`):
  - `rich`
  - `tqdm`

---

## Notes

- **Security:** Your email and password are only used for logging into your email account via IMAP. Ensure you trust the environment in which you run this tool.
- **Email Compatibility:** Tested with Gmail and Yahoo. Other IMAP services may require additional configuration.

---

Feel free to open issues or contribute to the project by submitting pull requests. 🚀
