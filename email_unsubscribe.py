import imaplib
import email
from email.header import decode_header
import sys
import re
import webbrowser
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

# Constants for IMAP servers
IMAP_SERVERS = {
    "gmail.com": "imap.gmail.com",
    "yahoo.com": "imap.mail.yahoo.com",
}

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

def fetch_emails(mail, num_emails):
    """Fetch emails from the inbox and extract unsubscribe links."""
    mail.select("inbox")

    # Search for all emails
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        console.print("[red]Failed to fetch emails.[/red]")
        return []

    email_ids = messages[0].split()
    emails = []

    for email_id in email_ids[-num_emails:]:  # Fetch the specified number of emails
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            continue

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_header(msg["Subject"])[0][0]
                subject = subject.decode() if isinstance(subject, bytes) else subject
                sender = decode_header(msg["From"])[0][0]
                sender = sender.decode() if isinstance(sender, bytes) else sender

                # Remove <email@domain.com> from the sender field
                sender = re.sub(r"<.*?>", "", sender).strip()

                # Extract email address
                match = re.search(r"<(.*?)>", msg["From"])
                sender_email = match.group(1) if match else msg["From"]

                # Extract unsubscribe links
                unsubscribe_links = extract_unsubscribe_links(msg)

                emails.append({
                    "subject": subject,
                    "sender": sender,
                    "email": sender_email,
                    "unsubscribe_links": unsubscribe_links,
                    "raw_msg": msg,  # Store raw message for debugging
                })
    return emails


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
        choice = Prompt.ask("Select an email index to open the unsubscribe link (or type 'exit' to quit)")

        if choice.lower() == "exit":
            console.print("[green]Goodbye![/green]")
            break

        if not choice.isdigit() or int(choice) < 0 or int(choice) >= len(emails):
            console.print("[red]Invalid choice. Try again.[/red]")
            continue

        email_choice = emails[int(choice)]
        unsubscribe_links = email_choice.get("unsubscribe_links")
        if unsubscribe_links:
            for link in unsubscribe_links:
                console.print(f"[green]Opening unsubscribe link: {link}[/green]")
                webbrowser.open(link)
        else:
            console.print("[red]No unsubscribe links found for this email.[/red]")
            debug_email(email_choice)

if __name__ == "__main__":
    main()
