# chat_evaluator.py (Part 1)
import re
from datetime import datetime
from collections import defaultdict
import spacy
import logging

# Initialize logger
logger = logging.getLogger(__name__)
# Set a more verbose logging level for debugging:
logger.setLevel(logging.DEBUG)  # Use DEBUG for detailed logging
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Load spaCy model for English *outside* the function, at the module level.
# This is the crucial change.
nlp = spacy.load("en_core_web_sm")

# --- Configuration Constants ---
MIN_WORDS = 5                # Minimum words required for a message to be considered
MIN_LENGTH_FOR_BONUS = 20    # Words beyond this count yield extra bonus
TACTICAL_PHRASES = [
    "win-win", "let's find a win-win solution", "what is your bottom line",
    "that's not acceptable", "I'm open to compromise",
    "we need to find common ground", "I have other options",
    "our alternative is", "let's negotiate", "how flexible are you",
    "we need to be fair", "I'm not willing to go lower", "that's a hard limit",
    "I appreciate your position", "let's work together",
    "can you do any better", "we're not in agreement",
    "let's reframe the issue", "I need a better offer",
    "this is our target", "our proposal is", "let's look at the numbers",
    "I want to see some concessions", "I'm prepared to make concessions",
    "what's your reservation price", "let's be realistic",
    "we need to move forward", "let's consider the long term",
    "I understand your concerns", "that's a fair point",
    "I can meet you halfway", "let's re-evaluate",
    "I'm not comfortable with that", "I believe there's room to improve",
    "this offer is below my expectations", "we need to build value",
    "let's get creative", "I propose an alternative", "that's a good start",
    "we need to think outside the box",
    "I'm looking for a mutually beneficial deal",
    "let's not leave money on the table", "we need to make this work",
    "let's break down the numbers", "I'm confident we can agree",
    "what if we adjust", "let's explore that option",
    "I'm under pressure to decide", "I need to see more",
    "that's below market value", "my benchmark suggests",
    "I have to consider my alternatives", "can you sweeten the deal",
    "we need to reach a consensus", "this doesn't meet our needs",
    "we can improve on that", "I'm prepared to negotiate",
    "we must be competitive", "I need a final offer", "let's settle this",
    "time is of the essence", "I need to know your best price",
    "we're close, but not there yet", "I expect more", "that falls short",
    "let's aim higher", "that's a starting point", "I can do better",
    "I'm willing to consider that", "I respect your position",
    "let's finalize the details", "that's a strong proposal",
    "we need to consider all options", "what do you propose",
    "we need a clear agreement", "I'm not satisfied with this",
    "let's make this a win-win", "this is my bottom line", "that's my minimum",
    "I need a competitive offer", "this is non-negotiable",
    "I can't agree to that", "we must compromise", "let's take a step back",
    "we need to reassess", "I think we can do better",
    "let's refine the proposal",
    "I'm interested, but not at that price", "let's keep negotiating",
    "I value your partnership", "we need to align our interests",
    "that's not sufficient", "I'm looking for a fair deal",
    "let's push the envelope", "we have room to maneuver",
    "your offer is too low", "I can work with that", "let's bridge the gap",
    "I need a sign of commitment", "we have to get this right"
]

BASE_TACTIC_BONUS = 5        # Base bonus per unique tactical phrase found
TACTICAL_RATIO_THRESHOLD = 0.4  # Maximum allowed ratio of tactical words to total words
EXTRA_BONUS_PER_WORD = 1     # Bonus per extra word beyond MIN_LENGTH_FOR_BONUS
PUNCTUATION_REGEX = r"[.!?]"  # Used to check for proper sentence termination
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
    """
    logger.debug(f"is_sentence_coherent: called with sent: {sent}")
    has_subject = any(token.dep_ in ("nsubj", "nsubjpass") for token in sent)
    has_verb = any(token.pos_ == "VERB" for token in sent)
    logger.debug(f"is_sentence_coherent: returning {(has_subject and has_verb)}")
    return has_subject and has_verb

def compute_coherence_factor(doc):
    """Compute the coherence factor for a spaCy Doc."""
    logger.debug(f"compute_coherence_factor: called with doc: {doc}")
    sentences = list(doc.sents)
    if not sentences:
        logger.debug("compute_coherence_factor: returning 0.0 (no sentences)")
        return 0.0
    coherent_count = sum(1 for sent in sentences if is_sentence_coherent(sent))
    factor = coherent_count / len(sentences)
    logger.debug(f"compute_coherence_factor: returning {factor}")
    return factor

# chat_evaluator.py (Part 2)

def evaluate_message(message_text: str) -> float:
    logger.debug(f"evaluate_message: called with message_text: {message_text}")
    text = message_text.strip()
    if not text:
        logger.debug("evaluate_message: returning 0.0 (empty text)")
        return 0.0

    doc = nlp(text)
    words = [token.text for token in doc if not token.is_space]
    word_count = len(words)
    if word_count < MIN_WORDS:
        logger.debug(f"evaluate_message: returning 0.0 (word_count < {MIN_WORDS})")
        return 0.0

    has_punctuation = bool(re.search(PUNCTUATION_REGEX, text))
    quality_factor = GOOD_QUALITY_FACTOR if has_punctuation else LOW_QUALITY_FACTOR
    logger.debug(f"evaluate_message: quality_factor: {quality_factor}")

    coherence_factor = compute_coherence_factor(doc)
    logger.debug(f"evaluate_message: coherence_factor: {coherence_factor}")

    if coherence_factor < COHERENCE_THRESHOLD:
        coherence_multiplier = coherence_factor
    else:
        coherence_multiplier = 1.0
    logger.debug(f"evaluate_message: coherence_multiplier: {coherence_multiplier}")

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
    logger.debug(f"evaluate_message: base_bonus: {base_bonus}")

    extra_words = max(0, word_count - MIN_LENGTH_FOR_BONUS)
    length_bonus = EXTRA_BONUS_PER_WORD * extra_words
    logger.debug(f"evaluate_message: length_bonus: {length_bonus}")

    tactical_ratio = tactical_word_count / word_count
    if tactical_ratio > TACTICAL_RATIO_THRESHOLD:
        discount_factor = TACTICAL_RATIO_THRESHOLD / tactical_ratio
    else:
        discount_factor = 1.0
    logger.debug(f"evaluate_message: discount_factor: {discount_factor}")

    message_score = (base_bonus + length_bonus) * quality_factor * discount_factor * coherence_multiplier
    logger.debug(f"evaluate_message: returning {message_score}")
    return message_score

def normalize_message(text: str) -> str:
    """Normalize message text."""
    logger.debug(f"normalize_message: called with text: {text}")
    text = text.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', text)
    logger.debug(f"normalize_message: returning {normalized}")
    return normalized

def group_messages_by_minute(chat_log, player_id):
    """Group messages by minute."""
    logger.debug(f"group_messages_by_minute: called with player_id: {player_id}")
    groups = defaultdict(list)
    seen_in_minute = defaultdict(set)
    for message in chat_log:
        #logger.debug(f"Processing message: {message}") #Log every message
        try:
            if str(message.get("sender")) != str(player_id):
                continue

            text = message.get("text", "").strip()
            if not text or len(re.split(r'\s+', text)) < MIN_WORDS:
                continue

            ts = message.get("timestamp")
            if not ts:
                logger.warning(f"Message without timestamp: {message}")
                minute_str = "unknown"
            else:
                try:
                    dt = datetime.fromisoformat(ts)
                    minute_str = dt.strftime("%Y-%m-%dT%H:%M")
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid timestamp format: {ts}")
                    minute_str = "unknown"

            normalized_text = normalize_message(text)
            if normalized_text in seen_in_minute[minute_str]:
                continue

            seen_in_minute[minute_str].add(normalized_text)
            groups[minute_str].append(message)

        except Exception as e:
            logger.error(f"Error processing message: {message}, Error: {e}")
            continue

    logger.debug(f"group_messages_by_minute: returning {groups}")
    return groups


def evaluate_chat(chat_log, player_id):
    """Evaluate full chat log."""
    logger.debug(f"evaluate_chat: called with player_id: {player_id}")
    try:
        logger.debug(f"Chat log for evaluation: {chat_log}")  # Log the chat log
        groups = group_messages_by_minute(chat_log, player_id)
        total_bonus = 0.0
        total_words = 0
        total_messages = 0

        for minute, messages in groups.items():
            try:
                max_score = 0.0
                for msg in messages:
                    text = msg.get("text", "").strip()
                    score = evaluate_message(text)
                    max_score = max(max_score, score)
                    word_count = len(re.split(r'\s+', text))
                    total_words += word_count
                    total_messages += 1
                total_bonus += min(max_score, MAX_BONUS_PER_MINUTE)
            except Exception as e:
                logger.error(f"Error processing minute {minute}: {e}")
                continue

        if total_messages > 0:
            avg_word_count = total_words / total_messages
            quality_multiplier = min(1.0, avg_word_count / MIN_AVERAGE_WORD_COUNT)
        else:
            quality_multiplier = 0.0
        logger.debug(f"Quality Multiplier: {quality_multiplier}")

        total_bonus *= quality_multiplier
        logger.debug(f"evaluate_chat: returning {int(round(total_bonus))}")
        return int(round(total_bonus))

    except Exception as e:
        logger.exception(f"Error evaluating chat: {e}")  # Use logger.exception
        return 0