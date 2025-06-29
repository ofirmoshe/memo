#!/usr/bin/env python3
"""
Test script for the new intent detection system.
This demonstrates how the bot will classify different types of messages.
"""

import re

def detect_user_intent(text: str) -> str:
    """
    Detect user intent from message text.
    
    Returns:
        'search' - User wants to search for content
        'save' - User wants to save content
        'greeting' - Casual greeting/conversation
        'url' - Contains URL (handled separately)
    """
    # Remove extra whitespace and convert to lowercase for analysis
    clean_text = text.strip().lower()
    
    # First check for URLs (highest priority)
    if re.search(r'https?://', text):
        return 'url'
    
    # Check for explicit search intent patterns
    search_patterns = [
        # Direct search requests
        r'^(find|search|look for|show me|get me|where is|do you have)',
        r'^(what.*saved|what.*remember|what.*stored)',
        r'(find|search|look for|show me|get me).*\b(post|article|video|image|document|note|content|item)',
        
        # Question patterns that indicate search
        r'^(what|where|when|how|which).*\?',
        r'^(do you have|is there|are there|can you find)',
        r'^(show|display|list).*\b(all|my|the)',
        
        # Content-specific search patterns
        r'\b(posts?|articles?|videos?|images?|documents?|notes?|content|items?)\b.*\b(about|on|related to|regarding)',
        r'\b(anything|something|content|items?)\b.*(about|on|related to|regarding)',
        
        # Memory/recall patterns - but NOT when starting with "remember to"
        r'^(recall|what was|remind me)',
        r'\b(saved|stored|remembered)\b.*\b(about|on|related to|regarding)',
    ]
    
    for pattern in search_patterns:
        if re.search(pattern, clean_text):
            return 'search'
    
    # Check for casual/greeting patterns
    greeting_patterns = [
        r'^(hi|hello|hey|yo|sup|hiya|howdy)$',
        r'^(good morning|good afternoon|good evening|good night)$',
        r'^(morning|afternoon|evening|night)$',
        r'^(ok|okay|yes|no|yeah|yep|nope|sure|thanks|thank you|thx)$',
        r'^(cool|nice|great|awesome|perfect|sounds good)$',
        r'^(test|testing|hello world)$',
        r'^(what|why|how|when|where|who)$',
        r'^[😀-🙏🏻]+$',  # Just emojis
        r'^(lol|lmao|haha|hehe|hmm|uhh|umm)$',
    ]
    
    for pattern in greeting_patterns:
        if re.search(pattern, clean_text):
            return 'greeting'
    
    # Check for save intent patterns
    save_patterns = [
        # Explicit save requests - including "remember to"
        r'^(save|remember|store|keep|note)',
        r'^(i want to|i need to|let me).*(save|remember|store|keep|note)',
        
        # Imperative statements that suggest saving
        r'^(this is|here is|check this)',
        r'^(important|reminder|todo|task)',
        
        # Personal notes/thoughts
        r'^(i think|i believe|my opinion|my thought)',
        r'^(idea:|thought:|note:|reminder:)',
        
        # Content sharing with context
        r'\b(for later|for reference|worth remembering|important)',
        r'\b(project|work|study|research)',
    ]
    
    for pattern in save_patterns:
        if re.search(pattern, clean_text):
            return 'save'
    
    # Heuristic: Longer, descriptive messages are likely to be content worth saving
    # But shorter queries might be searches
    if len(clean_text) > 50:
        # Long messages are more likely to be content to save
        return 'save'
    elif len(clean_text) > 10:
        # Medium messages - check for search-like keywords
        search_keywords = ['posts', 'articles', 'videos', 'images', 'content', 'about', 'related', 'decor', 'recipes', 'tutorials']
        if any(keyword in clean_text for keyword in search_keywords):
            return 'search'
        else:
            return 'save'
    else:
        # Short messages - check if they're search-like single keywords
        search_single_keywords = ['posts', 'articles', 'videos', 'images', 'content', 'decor', 'recipes', 'tutorials', 'programming', 'cooking', 'travel', 'fitness']
        if clean_text in search_single_keywords:
            return 'search'
        else:
            # Short messages are likely greetings or unclear
            return 'greeting'

def test_intent_detection():
    """Test the intent detection with various examples."""
    
    test_cases = [
        # Search examples
        ("home decor posts", "search"),
        ("find posts about cooking", "search"),
        ("show me articles on Python", "search"),
        ("do you have any videos about travel?", "search"),
        ("what did I save about AI?", "search"),
        ("look for content related to fitness", "search"),
        ("anything about recipes", "search"),
        ("posts about home improvement", "search"),
        ("videos about programming", "search"),
        
        # Save examples
        ("Remember to buy groceries tomorrow", "save"),
        ("This is an important meeting note", "save"),
        ("I think this approach works better for our project", "save"),
        ("Note: the deadline is next Friday", "save"),
        ("Important reminder about the client call", "save"),
        ("Here's a useful technique I learned today", "save"),
        ("Task: review the contract documents", "save"),
        
        # URL examples
        ("https://example.com check this out", "url"),
        ("Look at this: https://youtube.com/watch?v=123", "url"),
        ("https://github.com/user/repo for my project", "url"),
        
        # Greeting examples
        ("hi", "greeting"),
        ("hello", "greeting"),
        ("thanks", "greeting"),
        ("good morning", "greeting"),
        ("ok", "greeting"),
        ("cool", "greeting"),
        ("test", "greeting"),
        
        # Edge cases
        ("", "greeting"),
        ("what", "greeting"),
        ("videos", "search"),  # Single keyword should be search
        ("programming tutorials", "search"),  # Search-like keywords
        ("my thoughts on the new framework", "save"),  # Longer content
    ]
    
    print("🧠 Intent Detection Test Results")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for message, expected in test_cases:
        detected = detect_user_intent(message)
        status = "✅" if detected == expected else "❌"
        
        print(f"{status} '{message}' -> {detected} (expected: {expected})")
        
        if detected == expected:
            correct += 1
    
    print("=" * 50)
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    
    print("\n🔍 Interactive Test")
    print("Enter messages to test intent detection (type 'quit' to exit):")
    
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            intent = detect_user_intent(user_input)
            print(f"Intent: {intent}")
            
            # Show what the bot would do
            if intent == 'search':
                print("🔍 Bot would: Perform search")
            elif intent == 'save':
                print("💾 Bot would: Save as content")
            elif intent == 'url':
                print("🔗 Bot would: Extract and save URL")
            elif intent == 'greeting':
                print("👋 Bot would: Send casual response")
            
        except KeyboardInterrupt:
            break
    
    print("\nTest completed! 🚀")

if __name__ == "__main__":
    test_intent_detection() 