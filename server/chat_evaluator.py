import re
from datetime import datetime
from collections import defaultdict
import spacy

# Load spaCy model for English
nlp = spacy.load("en_core_web_sm")

# --- Configuration Constants ---
MIN_WORDS = 5                # Minimum words required for a message to be considered
MIN_LENGTH_FOR_BONUS = 20    # Words beyond this count yield extra bonus
TACTICAL_PHRASES = [
    "win-win",
    "let's find a win-win solution",
    "what is your bottom line",
    "that's not acceptable",
    "I'm open to compromise",
    "we need to find common ground",
    "I have other options",
    "our alternative is",
    "let's negotiate",
    "how flexible are you",
    "we need to be fair",
    "I'm not willing to go lower",
    "that's a hard limit",
    "I appreciate your position",
    "let's work together",
    "can you do any better",
    "we're not in agreement",
    "let's reframe the issue",
    "I need a better offer",
    "this is our target",
    "our proposal is",
    "let's look at the numbers",
    "I want to see some concessions",
    "I'm prepared to make concessions",
    "what's your reservation price",
    "let's be realistic",
    "we need to move forward",
    "let's consider the long term",
    "I understand your concerns",
    "that's a fair point",
    "I can meet you halfway",
    "let's re-evaluate",
    "I'm not comfortable with that",
    "I believe there's room to improve",
    "this offer is below my expectations",
    "we need to build value",
    "let's get creative",
    "I propose an alternative",
    "that's a good start",
    "we need to think outside the box",
    "I'm looking for a mutually beneficial deal",
    "let's not leave money on the table",
    "we need to make this work",
    "let's break down the numbers",
    "I'm confident we can agree",
    "what if we adjust",
    "let's explore that option",
    "I'm under pressure to decide",
    "I need to see more",
    "that's below market value",
    "my benchmark suggests",
    "I have to consider my alternatives",
    "can you sweeten the deal",
    "we need to reach a consensus",
    "this doesn't meet our needs",
    "we can improve on that",
    "I'm prepared to negotiate",
    "we must be competitive",
    "I need a final offer",
    "let's settle this",
    "time is of the essence",
    "I need to know your best price",
    "we're close, but not there yet",
    "I expect more",
    "that falls short",
    "let's aim higher",
    "that's a starting point",
    "I can do better",
    "I'm willing to consider that",
    "I respect your position",
    "let's finalize the details",
    "that's a strong proposal",
    "we need to consider all options",
    "what do you propose",
    "we need a clear agreement",
    "I'm not satisfied with this",
    "let's make this a win-win",
    "this is my bottom line",
    "that's my minimum",
    "I need a competitive offer",
    "this is non-negotiable",
    "I can't agree to that",
    "we must compromise",
    "let's take a step back",
    "we need to reassess",
    "I think we can do better",
    "let's refine the proposal",
    "I'm interested, but not at that price",
    "let's keep negotiating",
    "I value your partnership",
    "we need to align our interests",
    "that's not sufficient",
    "I'm looking for a fair deal",
    "let's push the envelope",
    "we have room to maneuver",
    "your offer is too low",
    "I can work with that",
    "let's bridge the gap",
    "I need a sign of commitment",
    "we have to get this right"
]

BASE_TACTIC_BONUS = 5        # Base bonus per unique tactical phrase found
TACTICAL_RATIO_THRESHOLD = 0.4  # Maximum allowed ratio of tactical words to total words
EXTRA_BONUS_PER_WORD = 1     # Bonus per extra word beyond MIN_LENGTH_FOR_BONUS
PUNCTUATION_REGEX = r"[.!?]" # Used to check for proper sentence termination
GOOD_QUALITY_FACTOR = 1.0
LOW_QUALITY_FACTOR = 0.5
MIN_AVERAGE_WORD_COUNT = 10  # Minimum average word count across messages to earn bonus
MAX_BONUS_PER_MINUTE = 15    # Cap bonus per minute

# --- Coherence Configuration ---
# We require that a message's sentences be "coherent"
# A sentence is considered coherent if it contains at least one nominal subject and one verb.
COHERENCE_THRESHOLD = 0.5  # At least 50% of sentences must be coherent for full bonus
MIN_COHERENCE_FACTOR = 0.0   # If no sentence is coherent, no bonus is awarded

def is_sentence_coherent(sent):
    """
    Check if a sentence (a spaCy Span) is coherent.
    We define a coherent sentence as one that contains at least one nominal subject and at least one verb.
    """
    has_subject = any(token.dep_ in ("nsubj", "nsubjpass") for token in sent)
    has_verb = any(token.pos_ == "VERB" for token in sent)
    return has_subject and has_verb

def compute_coherence_factor(doc):
    """
    Compute the coherence factor for a spaCy Doc.
    Factor = (number of coherent sentences) / (total number of sentences)
    If no sentences are found, return 0.
    """
    sentences = list(doc.sents)
    if not sentences:
        return 0.0
    coherent_count = sum(1 for sent in sentences if is_sentence_coherent(sent))
    return coherent_count / len(sentences)

def evaluate_message(message_text: str) -> float:
    """
    Evaluate a single message's bonus score using several heuristics:
    
    1. Message Quality: Must have at least MIN_WORDS.
    2. Sentence Structure: Must contain punctuation (as a proxy) and be parsed into coherent sentences.
       A coherence factor is computed based on the percentage of coherent sentences.
    3. Tactical Content: Awards points for unique tactical phrases (from TACTICAL_PHRASES).
    4. Length Bonus: Awards extra points for words beyond MIN_LENGTH_FOR_BONUS.
    5. Tactical Overuse Discount: If tactical words dominate the message, bonus is scaled down.
    
    Returns:
      float: The computed bonus score for the message.
    """
    text = message_text.strip()
    if not text:
        return 0.0

    # Process text using spaCy
    doc = nlp(text)
    words = [token.text for token in doc if not token.is_space]
    word_count = len(words)
    if word_count < MIN_WORDS:
        return 0.0  # Ignore messages that are too short

    # Check for punctuation; assume proper sentences if punctuation exists.
    has_punctuation = bool(re.search(PUNCTUATION_REGEX, text))
    quality_factor = GOOD_QUALITY_FACTOR if has_punctuation else LOW_QUALITY_FACTOR

    # Compute a coherence factor from sentence analysis.
    coherence_factor = compute_coherence_factor(doc)
    # If coherence is very low (e.g., less than the threshold), apply a penalty.
    if coherence_factor < COHERENCE_THRESHOLD:
        # Scale down bonus proportionally to the coherence ratio.
        coherence_multiplier = coherence_factor  # between 0 and 0.5
    else:
        coherence_multiplier = 1.0

    # Count tactical keywords using case-insensitive matching.
    text_lower = text.lower()
    unique_tactics = set()
    tactical_word_count = 0
    for phrase in TACTICAL_PHRASES:
        pattern = r'\b' + re.escape(phrase) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            unique_tactics.add(phrase)
            tactical_word_count += len(matches)
    base_bonus = BASE_TACTIC_BONUS * len(unique_tactics)

    # Extra bonus for length beyond MIN_LENGTH_FOR_BONUS.
    extra_words = max(0, word_count - MIN_LENGTH_FOR_BONUS)
    length_bonus = EXTRA_BONUS_PER_WORD * extra_words

    # Compute tactical ratio: tactical words / total words.
    tactical_ratio = tactical_word_count / word_count
    if tactical_ratio > TACTICAL_RATIO_THRESHOLD:
        discount_factor = TACTICAL_RATIO_THRESHOLD / tactical_ratio  # < 1
    else:
        discount_factor = 1.0

    # Final message score is the sum of tactical bonus and length bonus, scaled by quality, coherence, and discount factors.
    message_score = (base_bonus + length_bonus) * quality_factor * discount_factor * coherence_multiplier

    return message_score

def normalize_message(text: str) -> str:
    """
    Normalize the message text by converting to lowercase and removing punctuation.
    """
    text = text.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', text)
    return normalized

def group_messages_by_minute(chat_log, player_id):
    """
    Group messages from a specific player by minute using ISO‑8601 timestamps.
    Duplicate messages (after normalization) within the same minute are ignored.
    
    Returns:
      dict: Keys are minute strings (e.g., "2023-01-01T10:00") and values are lists of messages.
    """
    groups = defaultdict(list)
    seen_in_minute = defaultdict(set)
    for message in chat_log:
        if str(message.get("sender")) != str(player_id):
            continue
        text = message.get("text", "").strip()
        if len(re.split(r'\s+', text)) < MIN_WORDS:
            continue
        ts = message.get("timestamp")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                minute_str = dt.strftime("%Y-%m-%dT%H:%M")
            except Exception:
                minute_str = "unknown"
        else:
            minute_str = "unknown"
        normalized_text = normalize_message(text)
        if normalized_text in seen_in_minute[minute_str]:
            continue
        seen_in_minute[minute_str].add(normalized_text)
        groups[minute_str].append(message)
    return groups

def evaluate_chat(chat_log, player_id):
    """
    Evaluate the full chat log for a given player and compute a bonus score.
    
    Steps:
      1. Group messages by minute (using timestamps).
      2. For each minute, compute the bonus score for each message (using evaluate_message).
         Only the highest-scoring message in each minute is counted (to rate-limit bonus accumulation).
      3. Sum these per-minute scores.
      4. Adjust the overall bonus by the average word count across messages (if below a threshold, scale down).
    
    Returns:
      int: The final bonus score.
    """
    groups = group_messages_by_minute(chat_log, player_id)
    total_bonus = 0.0
    total_words = 0
    total_messages = 0

    for minute, messages in groups.items():
        max_score = 0.0
        for msg in messages:
            score = evaluate_message(msg.get("text", ""))
            max_score = max(max_score, score)
            word_count = len(re.split(r'\s+', msg.get("text", "").strip()))
            total_words += word_count
            total_messages += 1
        total_bonus += min(max_score, MAX_BONUS_PER_MINUTE)
    
    if total_messages > 0:
        avg_word_count = total_words / total_messages
        quality_multiplier = avg_word_count / MIN_AVERAGE_WORD_COUNT if avg_word_count < MIN_AVERAGE_WORD_COUNT else 1.0
    else:
        quality_multiplier = 0.0

    total_bonus *= quality_multiplier
    return int(round(total_bonus))

# --- Example usage ---
if __name__ == "__main__":
    example_chat_log = [
        {"sender": "1", "text": "I think we should aim for a win-win solution given the current market conditions. Our benchmarks indicate flexibility is key.", "timestamp": "2023-01-01T10:00:15"},
        {"sender": "1", "text": "Also, I believe anchoring our offer around industry averages will yield a fair compromise.", "timestamp": "2023-01-01T10:00:45"},
        {"sender": "1", "text": "Short msg", "timestamp": "2023-01-01T10:01:10"},
        {"sender": "1", "text": "Considering our leverage, I propose that we explore a trade-off where we make a concession on bonus in exchange for more remote days. This is a win-win strategy.", "timestamp": "2023-01-01T10:02:30"},
        {"sender": "2", "text": "Unrelated message from opponent.", "timestamp": "2023-01-01T10:03:00"},
        # A spammy message that uses tactical words but lacks coherent sentence structure:
        {"sender": "1", "text": "win-win haha haha benchmark poo poo", "timestamp": "2023-01-01T10:03:30"},
    ]
    player_id = "1"
    bonus_score = evaluate_chat(example_chat_log, player_id)
    print("Chat Bonus Score for player", player_id, ":", bonus_score)