from typing import Dict, List, Optional


class Accountant:
    """
    Personal accounting helper.

    Phrases: accountant, budget helper, ledger, expense tracker, finance helper,
    money tracker, spending tracker, income tracker, budget manager.

    Notes:
    - Stores everything in memory.
    - Designed for NLP phrase matching + parameter binding tests.
    - Docstrings intentionally include many natural-language phrases.
    """

    def __init__(self, owner_name: str = "Demo User"):
        """
        Create a new accountant instance.

        Phrases: create accountant, new accountant, start accountant, initialize accountant,
        make accountant, make a new accountant, open ledger, start ledger, init finance helper.

        Args:
            owner_name (str): the account owner's name.
        """
        self.owner_name = owner_name
        self.entries: List[dict] = []
        self.budgets: Dict[str, int] = {}
        self.tags: Dict[str, List[str]] = {}
        print(f"[INIT] Accountant created for owner: {owner_name}")

    # ------------------------------------------------------------
    # Core recording actions
    # ------------------------------------------------------------

    def add_expense(self, amount: int, category: str):
        """
        Record an expense entry.

        Phrases: spend, spent, add expense, expense, pay, paid, buy, bought,
        log expense, record expense, charge, charged.
        Examples:
          - "spend 1200 rent"
          - "paid 50 food"
          - "buy 3000 groceries"
          - "add expense 999 travel"

        Args:
            amount (int): money spent (integer).
            category (str): category of expense (e.g., rent, food, travel).

        Returns:
            None
        """
        self.entries.append({
            "kind": "expense",
            "amount": amount,
            "category": category,
            "note": "",
            "recipient": None
        })
        print(f"[ADD_EXPENSE] amount={amount}, category={category}")

    def add_income(self, amount: int, category: str = "salary"):
        """
        Record an income entry.

        Phrases: add income, income, got paid, receive money, received money,
        salary, earned, earn, log income, record income.
        Examples:
          - "got paid 20000 salary"
          - "add income 5000 bonus"

        Args:
            amount (int): money received (integer).
            category (str): income category (default: salary).

        Returns:
            None
        """
        self.entries.append({
            "kind": "income",
            "amount": amount,
            "category": category,
            "note": "",
            "recipient": None
        })
        print(f"[ADD_INCOME] amount={amount}, category={category}")

    def transfer(self, amount: int, recipient: str):
        """
        Record a transfer to someone.

        Phrases: transfer, send money, send, pay to, send to, give money to,
        wire, remit, pay someone.
        Examples:
          - "transfer 500 to mom"
          - "send 2000 to bob"

        Args:
            amount (int): money sent (integer).
            recipient (str): who you sent to.

        Returns:
            None
        """
        self.entries.append({
            "kind": "transfer",
            "amount": amount,
            "category": "transfer",
            "note": "",
            "recipient": recipient
        })
        print(f"[TRANSFER] amount={amount}, recipient={recipient}")

    def add_note(self, note: str):
        """
        Add a note to the most recent entry.

        Phrases: add note, note, attach note, write note, add memo, memo, remark,
        comment, annotate, add comment.
        Examples:
          - "add note lunch with friend"
          - "note taxi to airport"
          - "attach note paid cash"

        Args:
            note (str): note text to attach.

        Returns:
            None

        Raises:
            ValueError: if there is no entry to attach the note to.
        """
        if not self.entries:
            raise ValueError("No entries exist to attach a note.")
        self.entries[-1]["note"] = note
        print(f"[ADD_NOTE] note='{note}'")

    # ------------------------------------------------------------
    # Budgeting
    # ------------------------------------------------------------

    def set_budget(self, category: str, amount: int):
        """
        Set a monthly budget limit for a category.

        Phrases: set budget, set monthly limit, monthly limit, budget limit,
        cap spending, limit spending, set limit, budget for, set budget for.
        Supports both word orders:
          - "set monthly limit rent 10000"
          - "set budget 3000 for food"
          - "set budget food 3000"
          - "budget limit travel 20000"

        Args:
            category (str): category name (e.g., rent, food).
            amount (int): monthly limit amount (integer).

        Returns:
            None
        """
        self.budgets[category.lower()] = amount
        print(f"[SET_BUDGET] category={category}, amount={amount}")

    def remaining_budget(self, category: str) -> int:
        """
        Get remaining budget for a category.

        Phrases: remaining budget, budget left, how much left, remaining limit,
        left to spend, how much can I spend, remaining.
        Examples:
          - "remaining budget rent"
          - "how much left for food"

        Args:
            category (str): category name.

        Returns:
            int: remaining amount (limit - spent).
        """
        cat = category.lower()
        limit = self.budgets.get(cat, 0)
        spent = sum(
            e["amount"]
            for e in self.entries
            if e["kind"] == "expense" and e["category"].lower() == cat
        )
        remaining = limit - spent
        print(f"[REMAINING_BUDGET] category={category}, remaining={remaining}")
        return remaining

    # ------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------

    def total_spent(self, category: str = "all") -> int:
        """
        Compute total spent.

        Phrases: total spent, spending total, total expense, sum expenses,
        how much did I spend, total spending.
        Examples:
          - "total spent"
          - "total spent food"
          - "how much did I spend on rent"

        Args:
            category (str): category name or "all".

        Returns:
            int: total spent amount.
        """
        if category.lower() == "all":
            total = sum(e["amount"] for e in self.entries if e["kind"] == "expense")
        else:
            cat = category.lower()
            total = sum(
                e["amount"]
                for e in self.entries
                if e["kind"] == "expense" and e["category"].lower() == cat
            )

        print(f"[TOTAL_SPENT] category={category}, total={total}")
        return total

    def total_income(self, category: str = "all") -> int:
        """
        Compute total income.

        Phrases: total income, income total, sum income, total received,
        how much did I earn, total earnings.
        Examples:
          - "total income"
          - "total income salary"

        Args:
            category (str): category name or "all".

        Returns:
            int: total income amount.
        """
        if category.lower() == "all":
            total = sum(e["amount"] for e in self.entries if e["kind"] == "income")
        else:
            cat = category.lower()
            total = sum(
                e["amount"]
                for e in self.entries
                if e["kind"] == "income" and e["category"].lower() == cat
            )

        print(f"[TOTAL_INCOME] category={category}, total={total}")
        return total

    def summary(self) -> str:
        """
        Return a human-readable summary.

        Phrases: summary, show summary, report, overview, quick report,
        show report, account summary, spending summary.
        Examples:
          - "summary"
          - "show report"
          - "overview"

        Returns:
            str: summary text (income/expense/net/entry count).
        """
        spent = self.total_spent("all")
        earned = self.total_income("all")
        net = earned - spent

        summary_text = (
            f"Owner={self.owner_name} | "
            f"income={earned} | "
            f"expense={spent} | "
            f"net={net} | "
            f"entries={len(self.entries)}"
        )

        print(f"[SUMMARY] {summary_text}")
        return summary_text

    # ------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------

    def clear_entries(self):
        """
        Clear all entries.

        Phrases: clear entries, reset ledger, delete all entries,
        wipe history, clear history, reset history.

        WARNING: destructive.

        Returns:
            None
        """
        self.entries.clear()
        print("[CLEAR_ENTRIES] All entries removed")

    def tag_category(self, category: str, tag: str):
        """
        Add a tag to a category.

        Phrases: tag category, add tag, label category, categorize tag,
        put tag on, mark category.
        Examples:
          - "tag category food necessary"
          - "label category rent fixed"

        Args:
            category (str): category name.
            tag (str): tag label.

        Returns:
            None
        """
        cat = category.lower()
        self.tags.setdefault(cat, [])
        if tag.lower() not in self.tags[cat]:
            self.tags[cat].append(tag.lower())
        print(f"[TAG_CATEGORY] category={category}, tag={tag}")

    def list_entries(self, count: int = 5) -> List[dict]:
        """
        List recent entries.

        Phrases: list entries, show entries, recent entries, last entries,
        history, show history, show last entries.
        Examples:
          - "list entries"
          - "recent entries 10"
          - "show history"

        Args:
            count (int): number of recent entries.

        Returns:
            List[dict]: recent entries (each entry is a dict).
        """
        result = self.entries[-count:]
        print(f"[LIST_ENTRIES] count={count}, result={result}")
        return result