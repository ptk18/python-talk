import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.say("This is a simple text to speech test using pyttsx three.")
engine.runAndWait() # This is the command that blocks until the speech is complete

print("Speech complete.")