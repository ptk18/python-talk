class QuizGame:
    def start_game(self, difficulty):
        """Begin a new quiz game at the specified difficulty level."""
        return f"Quiz started at {difficulty} difficulty"

    def get_question(self):
        """Retrieve the current quiz question."""
        return "What is the capital of France?"

    def submit_answer(self, answer):
        """Submit an answer for the current question."""
        return f"Answer '{answer}' submitted. Correct!"

    def skip_question(self):
        """Skip the current question without answering."""
        return "Question skipped. Moving to next question."

    def use_hint(self):
        """Reveal a hint for the current question."""
        return "Hint: It starts with the letter P."

    def get_score(self):
        """Return the current score and statistics."""
        return {"correct": 7, "wrong": 2, "skipped": 1, "score": 70}

    def end_game(self):
        """Finish the game and calculate final results."""
        return "Game over! Final score: 70 out of 100"

    def get_leaderboard(self, top_n):
        """Return the top N players on the leaderboard."""
        return [f"Player {i+1}: {100 - i*10} pts" for i in range(top_n)]
