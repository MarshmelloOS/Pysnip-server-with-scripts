import time
import json

# Define the questions and answers
questions = [
    {"question": "What does 'Salut' in French mean?", "a": "Hello", "b": "Good", "c": "Honor", "correct": "a"},
    # Add more questions here...
]

# Define player scores
player_scores = {}

# Load player scores from JSON file
def load_scores():
    global player_scores
    try:
        with open("dist/playerscore.json", "r") as file:
            player_scores = json.load(file)
    except FileNotFoundError:
        pass

# Save player scores to JSON file
def save_scores():
    with open("dist/playerscore.json", "w") as file:
        json.dump(player_scores, file)

# Function to run the quiz
def run_quiz():
    load_scores()
    for question_data in questions:
        question = question_data["question"]
        options = ", ".join(["{}: {}".format(key, value) for key, value in question_data.items() if key != "correct"])
        correct_answer = question_data["correct"]
        
        print(question)
        print("Options:", options)

        # Countdown timer
        for i in range(30, 0, -1):
            if i <= 5:
                print("Time remaining:", i, "seconds")
            time.sleep(1)

        # Check answers
        for player in player_scores:
            print("Player", player, ": What's your answer? ('/a', '/b', '/c')")
            answer = input().strip().lower()
            if answer == correct_answer:
                print("Correct answer!")
                player_scores[player] += 5
            else:
                print("Wrong answer.")

    save_scores()

# Command handler for /quizscore or /qs
def quiz_score(player_ip):
    load_scores()
    score = player_scores.get(player_ip, 0)
    print("Your score is:", score)

# Example usage
# run_quiz()  # Uncomment this line to run the quiz

# Sample command handling
while True:
    command = input("Enter command: ").strip()
    if command == "/quiz":
        run_quiz()
    elif command in ("/quizscore", "/qs"):
        player_ip = input("Enter player's IP: ")
        quiz_score(player_ip)
    elif command == "/exit":
        break
