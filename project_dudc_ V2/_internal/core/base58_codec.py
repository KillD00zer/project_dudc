"""
DUDC Base58 Codec & Visual Group Formatter
==========================================
Encodes/decodes binary payloads to clean alphanumeric strings without confusing characters (0, O, I, l).
Formats output into readable 6-character blocks:
DUDC-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX
"""

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE = len(ALPHABET)
ALPHABET_INDEX = {char: idx for idx, char in enumerate(ALPHABET)}

def b58encode_int(number: int, min_length: int = 36) -> str:
    """Encode an integer to a fixed-length Base58 string with zero-padding."""
    if number == 0:
        return ALPHABET[0] * min_length
    
    chars = []
    val = number
    while val > 0:
        val, rem = divmod(val, BASE)
        chars.append(ALPHABET[rem])
    
    # Left-pad to min_length to ensure uniform 36-character length
    while len(chars) < min_length:
        chars.append(ALPHABET[0])
        
    return "".join(reversed(chars))

def b58decode_int(encoded: str) -> int:
    """Decode a Base58 string back to integer."""
    val = 0
    for char in encoded:
        if char not in ALPHABET_INDEX:
            raise ValueError(f"Invalid Base58 character: '{char}'")
        val = val * BASE + ALPHABET_INDEX[char]
    return val

def format_token(raw_b58: str, group_size: int = 6, prefix: str = "DUDC") -> str:
    """Format Base58 string into grouped blocks: DUDC-XXXXXX-XXXXXX-..."""
    groups = [raw_b58[i:i+group_size] for i in range(0, len(raw_b58), group_size)]
    formatted = "-".join(groups)
    if prefix:
        return f"{prefix}-{formatted}"
    return formatted

def parse_token(token: str) -> str:
    """Clean user input: strip prefix, spaces, hyphens, and return raw Base58 string."""
    clean = token.strip()
    if clean.upper().startswith("DUDC-") or clean.upper().startswith("DUDC "):
        clean = clean[5:]
    elif clean.upper().startswith("DUDC"):
        clean = clean[4:]
        
    clean = clean.replace("-", "").replace(" ", "").replace("_", "").strip()
    return clean
