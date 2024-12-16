import imaplib
import email
from email.header import decode_header
import sys
import re
import webbrowser
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from tqdm import tqdm


# Constants for IMAP servers
IMAP_SERVERS = {
    "gmail.com": "imap.gmail.com",
    "yahoo.com": "imap.mail.yahoo.com",
}

SKIP_FILE = "skipped_emails.txt"  # File to store skipped email addresses

console = Console()

def connect_to_email(email_address, password):
    domain = email_address.split("@")[-1]
    imap_server = IMAP_SERVERS.get(domain)

    if not imap_server:
        console.print(f"[red]Unsupported email domain: {domain}[/red]")
        sys.exit(1)

    # Connect to the IMAP server
    console.print(f"Connecting to {imap_server}...")
    mail = imaplib.IMAP4_SSL(imap_server)

    # Login
    try:
        mail.login(email_address, password)
    except imaplib.IMAP4.error as e:
        console.print(f"[red]Login failed: {e}[/red]")
        sys.exit(1)

    console.print("[green]Login successful![/green]")
    return mail

def extract_links_from_html(html):
    """Extract all links from HTML content and filter unsubscribe-related links."""
    # Extract all <a href="...">...</a> links
    all_links = re.findall(r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
    
    unsubscribe_links = []
    for url, text in all_links:
        # Include links if the text or URL contains "unsubscribe" or "click here"
        if "unsubscribe" in text.lower() or "click here" in text.lower() or "unsubscribe" in url.lower():
            unsubscribe_links.append(url)
    
    return unsubscribe_links

def extract_unsubscribe_links(msg):
    """Extract unsubscribe links from email headers and body."""
    unsubscribe_links = []

    # Check for List-Unsubscribe header
    list_unsubscribe = msg.get("List-Unsubscribe")
    if list_unsubscribe:
        # Extract HTTP/HTTPS links, skipping mailto links
        http_links = re.findall(r'<(https?://[^>]+)>', list_unsubscribe)
        unsubscribe_links.extend(http_links)

    # Check email body for unsubscribe links
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html":
                body = part.get_payload(decode=True).decode(errors="ignore")

                # Find unsubscribe links in the HTML content
                unsubscribe_links.extend(extract_links_from_html(body))
    else:
        # Single-part message
        content_type = msg.get_content_type()
        if content_type == "text/html":
            body = msg.get_payload(decode=True).decode(errors="ignore")

            # Find unsubscribe links in the HTML content
            unsubscribe_links.extend(extract_links_from_html(body))

    # Remove mailto: links and return unique HTTP/HTTPS links
    unsubscribe_links = [link for link in unsubscribe_links if not link.startswith("mailto:")]
    return list(set(unsubscribe_links))

def display_emails(emails):
    """Display the emails in a table with unsubscribe links."""
    total_emails = len(emails)
    successful_links = sum(1 for email in emails if email["unsubscribe_links"])

    table = Table(title=f"Emails with Unsubscribe Links ({successful_links}/{total_emails})")
    table.add_column("Index", justify="center")
    table.add_column("Sender", justify="left")
    table.add_column("Email", justify="left")
    table.add_column("Unsubscribe Links", justify="left")

    for idx, email in enumerate(emails):
        links = "\n".join(email["unsubscribe_links"]) if email["unsubscribe_links"] else "[red]No links found[/red]"
        table.add_row(
            str(idx),
            email["sender"],
            email["email"],
            links,
        )

    console.print(table)


def debug_email(email):
    """Print headers and body content for debugging."""
    console.print("[cyan]--- Debugging Information ---[/cyan]")

    # Print headers
    console.print("[cyan]Headers:[/cyan]")
    for header, value in email["raw_msg"].items():
        console.print(f"[yellow]{header}[/yellow]: {value}")

    # Print body content
    console.print("[cyan]Body Content:[/cyan]")
    if email["raw_msg"].is_multipart():
        for part in email["raw_msg"].walk():
            content_type = part.get_content_type()
            if content_type in ["text/plain", "text/html"]:
                body = part.get_payload(decode=True).decode(errors="ignore")
                console.print(f"[green]{content_type} (last 500 characters):[/green]")
                console.print(body[-500:])  # Print last 500 characters
    else:
        content_type = email["raw_msg"].get_content_type()
        if content_type in ["text/plain", "text/html"]:
            body = email["raw_msg"].get_payload(decode=True).decode(errors="ignore")
            console.print(f"[green]{content_type} (last 500 characters):[/green]")
            console.print(body[-500:])  # Print last 500 characters

import os

SKIP_FILE = "skipped_emails.txt"  # File to store skipped email addresses

def load_skipped_emails():
    """Load skipped emails from the text file."""
    if os.path.exists(SKIP_FILE):
        with open(SKIP_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_skipped_email(email):
    """Save a skipped email to the text file."""
    with open(SKIP_FILE, "a") as f:
        f.write(email + "\n")

def fetch_emails(mail, num_emails):
    """Fetch emails and ensure unique titles and links, skipping previously saved emails."""
    mail.select("inbox")

    # Search for all emails
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        console.print("[red]Failed to fetch emails.[/red]")
        return []

    email_ids = messages[0].split()
    total_emails = len(email_ids)
    fetched_emails = []
    unique_titles = set()
    skipped_emails = load_skipped_emails()
    emails_to_fetch = num_emails
    offset = 0  # Start fetching from the latest emails

    while len(fetched_emails) < num_emails and offset < total_emails:
        batch_size = min(emails_to_fetch, total_emails - offset)
        email_batch_ids = email_ids[-(offset + batch_size): -offset or None]  # Fetch in batches
        offset += batch_size

        console.print(f"[blue]Fetching a batch of {batch_size} emails...[/blue]")
        with tqdm(total=batch_size, desc="Fetching Emails", unit="email", file=sys.stdout) as pbar:
            for email_id in email_batch_ids:
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        console.print(f"[red]Error fetching email ID {email_id.decode()}[/red]")
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_header(msg["Subject"])[0][0]
                            subject = subject.decode() if isinstance(subject, bytes) else subject or "No Subject"

                            if subject in unique_titles:
                                continue  # Skip duplicates

                            sender = decode_header(msg["From"])[0][0]
                            sender = sender.decode() if isinstance(sender, bytes) else sender

                            # Remove email address in angle brackets and unwanted characters from sender name
                            sender = re.sub(r"<.*?>", "", sender).strip()
                            sender = re.sub(r'^"|"$', '', sender).strip()  # Remove leading/trailing quotes

                            # Extract email address
                            match = re.search(r"<(.*?)>", msg["From"])
                            sender_email = match.group(1) if match else msg["From"]

                            # Skip emails already marked in the skip file
                            if sender_email in skipped_emails:
                                continue

                            # Extract unsubscribe links
                            unsubscribe_links = list(set(extract_unsubscribe_links(msg)))

                            # Check if an identical entry (sender + unsubscribe links) exists
                            if any(email for email in fetched_emails if email["sender"] == sender and set(email["unsubscribe_links"]) == set(unsubscribe_links)):
                                continue  # Skip if an identical entry already exists

                            fetched_emails.append({
                                "subject": subject,
                                "sender": sender,
                                "email": sender_email,
                                "unsubscribe_links": unsubscribe_links,
                                "raw_msg": msg,  # Store raw message for debugging
                            })
                            unique_titles.add(subject)  # Mark this title as processed
                except Exception as e:
                    console.print(f"[red]Error fetching email ID {email_id.decode()}: {e}[/red]")
                finally:
                    pbar.update(1)

        # Adjust the number of emails to fetch based on unique titles found
        emails_to_fetch = num_emails - len(fetched_emails)

    # Sort emails alphabetically by sender
    fetched_emails = sorted(fetched_emails, key=lambda x: x["sender"])
    return fetched_emails[:num_emails]  # Return only the required number of emails


def main():
    if len(sys.argv) != 4:
        console.print("[red]Usage: python3 email_unsubscribe.py {email} {password} {items}[/red]")
        sys.exit(1)

    email_address = sys.argv[1]
    password = sys.argv[2]
    num_emails = int(sys.argv[3])

    mail = connect_to_email(email_address, password)
    emails = fetch_emails(mail, num_emails)
    mail.logout()

    if not emails:
        console.print("[yellow]No emails found with unsubscribe links.[/yellow]")
        return

    display_emails(emails)

    while True:
        choice = Prompt.ask("Select an email index to open the unsubscribe link, or type 'exit' to quit, or {index}-add to skip")

        if choice.lower() == "exit":
            console.print("[green]Goodbye![/green]")
            break

        # Check if the user wants to add an email to the skip file
        if "-add" in choice:
            try:
                idx = int(choice.split("-")[0])
                if 0 <= idx < len(emails):
                    email_choice = emails[idx]
                    save_skipped_email(email_choice["email"])
                    console.print(f"[green]Added {email_choice['email']} to the skip list.[/green]")
                    continue
                else:
                    console.print("[red]Invalid index. Try again.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Use the format {index}-add.[/red]")
                continue

        # Handle opening unsubscribe links
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(emails):
                email_choice = emails[idx]
                unsubscribe_links = email_choice.get("unsubscribe_links")
                if unsubscribe_links:
                    for link in unsubscribe_links:
                        console.print(f"[green]Opening unsubscribe link: {link}[/green]")
                        webbrowser.open(link)
                else:
                    console.print("[red]No unsubscribe links found for this email.[/red]")
                    debug_email(email_choice)
            else:
                console.print("[red]Invalid index. Try again.[/red]")
        else:
            console.print("[red]Invalid choice. Try again.[/red]")


if __name__ == "__main__":
    main()
