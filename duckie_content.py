# We import your memory file so Duckie can 'read' while he 'writes'
import memory

def generate_linkedin_post(project_name, features):
    """Creates a professional post layout."""
    post = f"""
🚀 Project Update: {project_name}
Built during our 24-hour hackathon!

Key Features:
✅ {features}

Stay tuned for the demo! #DuckieAI #Innovation #Coding
    """
    return post

def personalize_greeting():
    """Duckie looks up the user's name to say hello."""
    # We call the function you just built in the other file!
    name = memory.get_info("user_name")
    
    if name == "None":
        return "Hello! I am Duckie, your personal assistant. What is your name?"
    else:
        return f"Welcome back, {name}! How can I help you with your project today?"

def chain_prepare_post(topic, features):
    """A 'Task Chain': Creates a post and saves it to the brain immediately."""
    # 1. Write the post
    new_post = generate_linkedin_post(topic, features)
    
    # 2. Save it to the SQLite database
    memory.save_info("last_post_draft", new_post)
    
    return "I have drafted the post and saved it to my memory for you."