class EmailClient:
    def send_email(self, recipient, subject, body):
        """Send an email to the recipient with the given subject and body."""
        return f"Email sent to {recipient} with subject '{subject}'"

    def read_email(self, email_id):
        """Open and display the contents of an email."""
        return f"Email {email_id}: Subject - Meeting Tomorrow, Body - Please confirm attendance."

    def reply_to_email(self, email_id, message):
        """Reply to an existing email with a message."""
        return f"Reply sent to email {email_id}: '{message}'"

    def delete_email(self, email_id):
        """Delete an email from the inbox."""
        return f"Email {email_id} deleted"

    def search_emails(self, keyword):
        """Search all emails containing the specified keyword."""
        return [f"Email 3: '{keyword}' in subject", f"Email 7: '{keyword}' in body"]

    def mark_as_read(self, email_id):
        """Mark an email as read without opening it."""
        return f"Email {email_id} marked as read"

    def get_unread_count(self):
        """Return the number of unread emails in the inbox."""
        return 5

    def move_to_folder(self, email_id, folder_name):
        """Move an email to a specified folder."""
        return f"Email {email_id} moved to '{folder_name}' folder"
