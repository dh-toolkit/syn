#!/usr/bin/env python3
"""
AI Synonymizer - Scenario-Based Three-Phase Synonymization

Phase 1: Extract adjectives and meaning verbs (excluding named entities)
Phase 2: Generate one synonym per word with 1:1 mapping
Phase 3: Substitute words using position-based replacement

Usage:
    python synonymizer.py --text "Your text here" --api-key "your-key"
    python synonymizer.py --file input.txt --api-key "your-key" --output result.txt
    python synonymizer.py --text "Your text" --mode rewrite

Created: 2025
Based on: ai-paraphraser.php (Three-Phase Synonymization Algorithm)
Version: 1.0.0
"""

import os
import sys
import re
import json
import argparse
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SynonymizerConfig:
    """Configuration for the synonymizer"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        mode: str = "synonymize",
        temperature_extract: float = 0.2,
        temperature_synonymize: float = 0.5,
        temperature_substitute: float = 0.1,
        temperature_rewrite: float = 0.7,
        temperature_correct: float = 0.2,
        max_tokens_extract: int = 200,
        max_tokens_synonymize: int = 300,
        max_tokens_substitute: int = 1000,
        max_tokens_rewrite: int = 4000,
        timeout: int = 60,
        debug: bool = False
    ):
        self.api_key = api_key
        self.model = model
        self.mode = mode
        self.temperature_extract = temperature_extract
        self.temperature_synonymize = temperature_synonymize
        self.temperature_substitute = temperature_substitute
        self.temperature_rewrite = temperature_rewrite
        self.temperature_correct = temperature_correct
        self.max_tokens_extract = max_tokens_extract
        self.max_tokens_synonymize = max_tokens_synonymize
        self.max_tokens_substitute = max_tokens_substitute
        self.max_tokens_rewrite = max_tokens_rewrite
        self.timeout = timeout
        self.debug = debug


class OpenAIClient:
    """Client for OpenAI API interactions"""
    
    API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, api_key: str, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        })
    
    def call_api(
        self,
        system_prompt: str,
        user_content: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        """Make API call to OpenAI"""
        
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            response = self.session.post(
                self.API_URL,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"API error: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content.strip().strip('"\'')
            
            logger.error("Invalid API response format")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            return None


class ThreePhaseAlgorithm:
    """Three-phase synonymization algorithm"""
    
    def __init__(self, config: SynonymizerConfig):
        self.config = config
        self.client = OpenAIClient(config.api_key, config.timeout)
    
    def phase1_extract(self, text: str) -> List[str]:
        """
        PHASE 1: Extract adjectives and meaningful verbs
        
        Returns a list of words in order of appearance
        """
        if self.config.debug:
            logger.info("=" * 60)
            logger.info("PHASE 1: EXTRACT ADJECTIVES AND MEANING VERBS")
            logger.info(f"Text: {text}")
        
        system_prompt = (
            'You are a precise linguistic analyzer.\n\n'
            'Extract from the paragraph:\n'
            '1. ALL adjectives that are NOT part of any proper name or named entity\n'
            '   (e.g. recent, significant, next, ongoing, new).\n'
            '2. ALL verbs exactly as they appear in the text, including:\n'
            '   - Auxiliary verbs: have, has, had, is, was, were\n'
            '   - Main verbs: raised, caused, increased\n'
            '   - Past participles used as verbs: attributed, caused\n'
            '   - Present participles: indicating\n'
            '3. Action nouns — nouns that name a discrete action or event (attacks, closure).\n\n'
            'EXCLUDE completely:\n'
            '- Proper names and named entities (company names, places, people, product codes).\n'
            '- Regular and abstract nouns (market, effect, quarter, ton, industry, vulnerability,\n'
            '  deficiency, phase, projection, adjustment, damage, inventory, smelters, fluctuations).\n'
            '- Articles (a, an, the), prepositions, conjunctions, pronouns, adverbs.\n'
            '- Numbers, dates, currencies.\n\n'
            'Return ONLY the words exactly as they appear in the text, in order of appearance,\n'
            'separated by single spaces. No punctuation, no parentheses, no numbering, no explanations.'
        )
        
        result = self.client.call_api(
            system_prompt=system_prompt,
            user_content=text,
            model=self.config.model,
            temperature=self.config.temperature_extract,
            max_tokens=self.config.max_tokens_extract
        )
        
        if not result:
            logger.warning("Phase 1 failed, no words extracted")
            return []
        
        words = result.split()
        
        if self.config.debug:
            logger.info(f"Extracted {len(words)} words: {' '.join(words)}")
        
        return words
    
    def phase2_synonymize(self, words: List[str], context: str) -> List[str]:
        """
        PHASE 2: Generate one synonym per word in batch
        
        Returns parallel list of synonyms with 1:1 mapping
        """
        if self.config.debug:
            logger.info("=" * 60)
            logger.info("PHASE 2: GENERATE BATCH SYNONYMS (1:1 MAPPING)")
        
        if not words:
            if self.config.debug:
                logger.info("No words to synonymize")
            return []
        
        word_list = ' '.join(words)
        
        instruction = (
            'Write one synonym for each of the words listed below. '
            'Print ONLY the synonyms, one per line, in the exact same order as the input. '
            'No numbering, no punctuation, no explanations. '
            'Each synonym must match the grammatical form (tense, number) of the original word '
            'and fit naturally in the provided context.'
        )
        
        user_content = f'Context: "{context}"\n\nWords: {word_list}'
        
        result = self.client.call_api(
            system_prompt=instruction,
            user_content=user_content,
            model=self.config.model,
            temperature=self.config.temperature_synonymize,
            max_tokens=self.config.max_tokens_synonymize
        )
        
        if not result:
            logger.warning("Phase 2 failed, returning original words")
            return words
        
        # Parse synonyms from result (one per line)
        lines = [line.strip() for line in result.split('\n') if line.strip()]
        
        synonyms = []
        for line in lines:
            # Strip any accidental numbering: "1. latest" → "latest"
            synonym = re.sub(r'^\d+[\.\)]\s*', '', line)
            synonym = synonym.strip('"\'.,;:!?')
            synonyms.append(synonym)
        
        # Ensure we have the same number of synonyms as words
        word_count = len(words)
        synonym_count = len(synonyms)
        
        if synonym_count < word_count:
            logger.warning(
                f"Response has fewer synonyms ({synonym_count}) than words ({word_count}), "
                f"padding with originals"
            )
            synonyms.extend(words[synonym_count:])
        elif synonym_count > word_count:
            logger.warning(
                f"Response has more synonyms ({synonym_count}) than words ({word_count}), "
                f"trimming"
            )
            synonyms = synonyms[:word_count]
        
        if self.config.debug:
            logger.info("Synonym mapping:")
            for orig, syn in zip(words, synonyms):
                logger.info(f'  "{orig}" → "{syn}"')
        
        return synonyms
    
    def phase3_substitute(self, text: str, words: List[str], synonyms: List[str]) -> str:
        """
        PHASE 3: Ask LLM to substitute words with synonyms
        
        Returns the modified paragraph
        """
        if self.config.debug:
            logger.info("=" * 60)
            logger.info("PHASE 3: APPLY SUBSTITUTION VIA LLM")
            logger.info(f"Original: {text}")
        
        if not words or not synonyms or len(words) != len(synonyms):
            logger.error("Word/synonym array mismatch, returning original text")
            return text
        
        system_prompt = (
            'Substitute the words with their synonyms respectively in the paragraph. '
            'Replace each word in the "Original words" list with the corresponding word in the "Substitute with" list. '
            'Keep the same order. Preserve all punctuation, capitalization, and sentence structure. '
            'Return ONLY the modified paragraph, nothing else.'
        )
        
        user_content = (
            f'Paragraph: "{text}"\n\n'
            f'Original words: {" ".join(words)}\n\n'
            f'Substitute with: {" ".join(synonyms)}'
        )
        
        result = self.client.call_api(
            system_prompt=system_prompt,
            user_content=user_content,
            model=self.config.model,
            temperature=self.config.temperature_substitute,
            max_tokens=self.config.max_tokens_substitute
        )
        
        if not result:
            logger.warning("Phase 3 failed, returning original text")
            return text
        
        result = result.strip('"\'')
        
        if self.config.debug:
            logger.info(f"Result: {result}")
        
        return result
    
    def synonymize(self, text: str) -> str:
        """
        Main three-phase synonymization pipeline
        
        Exactly 3 API calls regardless of text length
        """
        logger.info("Starting three-phase synonymization")
        
        if self.config.debug:
            word_count = len(text.split())
            logger.info(f"Input ({word_count} words): {text}")
        
        # PHASE 1: Extract
        words = self.phase1_extract(text)
        
        if not words:
            logger.info("No candidates extracted, returning original text")
            return text
        
        # PHASE 2: Batch synonyms
        synonyms = self.phase2_synonymize(words, text)
        
        if not synonyms or len(synonyms) != len(words):
            logger.error("Synonym count mismatch, returning original text")
            return text
        
        # PHASE 3: LLM substitution
        result = self.phase3_substitute(text, words, synonyms)
        
        # Count actual changes
        changes = sum(1 for w, s in zip(words, synonyms) if w.lower() != s.lower())
        
        if self.config.debug:
            logger.info("=" * 60)
            logger.info("THREE-PHASE SYNONYMIZATION SUMMARY")
            logger.info(f"API calls used      : 3")
            logger.info(f"Words extracted     : {len(words)}")
            logger.info(f"Words substituted   : {changes}")
            logger.info(f"ORIGINAL: {text}")
            logger.info(f"RESULT  : {result}")
        
        logger.info(f"Synonymization complete - {changes} words changed")
        
        return result


class TextRewriter:
    """Simple text rewriting mode"""
    
    def __init__(self, config: SynonymizerConfig):
        self.config = config
        self.client = OpenAIClient(config.api_key, config.timeout)
    
    def rewrite(self, text: str, prompt: Optional[str] = None) -> str:
        """Rewrite text using AI"""
        
        if not prompt:
            prompt = (
                'Rewrite the following text while preserving its meaning. '
                'Make it more fluent and natural. Return only the rewritten text.'
            )
        
        # Replace placeholder if exists
        if '{{selected_text}}' in prompt:
            user_content = prompt.replace('{{selected_text}}', text)
            system_prompt = 'You are a professional text rewriter.'
        else:
            system_prompt = prompt
            user_content = text
        
        result = self.client.call_api(
            system_prompt=system_prompt,
            user_content=user_content,
            model=self.config.model,
            temperature=self.config.temperature_rewrite,
            max_tokens=self.config.max_tokens_rewrite
        )
        
        return result if result else text


class TextCorrector:
    """Optional correction pass for paraphrased text"""
    
    def __init__(self, config: SynonymizerConfig):
        self.config = config
        self.client = OpenAIClient(config.api_key, config.timeout)
    
    def correct(self, text: str, check_prompt: Optional[str] = None) -> str:
        """Check and correct paraphrased text"""
        
        if not check_prompt:
            check_prompt = (
                'Review the following text for grammatical correctness and fluency. '
                'Fix any errors while preserving the original meaning and style. '
                'Return only the corrected text.'
            )
        
        result = self.client.call_api(
            system_prompt=check_prompt,
            user_content=text,
            model=self.config.model,
            temperature=self.config.temperature_correct,
            max_tokens=self.config.max_tokens_rewrite
        )
        
        return result if result else text


class Synonymizer:
    """Main synonymizer class"""
    
    def __init__(self, config: SynonymizerConfig):
        self.config = config
        self.algorithm = ThreePhaseAlgorithm(config)
        self.rewriter = TextRewriter(config)
        self.corrector = TextCorrector(config)
    
    def process(
        self,
        text: str,
        mode: Optional[str] = None,
        rewrite_prompt: Optional[str] = None,
        check_prompt: Optional[str] = None,
        apply_correction: bool = False
    ) -> str:
        """
        Process text with specified mode
        
        Modes:
            - 'synonymize': Three-phase algorithm (default)
            - 'rewrite': AI rewrite
        """
        mode = mode or self.config.mode
        text = text.strip()
        
        if not text:
            return text
        
        # Process based on mode
        if mode == 'synonymize':
            logger.info("Using synonymize mode (three-phase algorithm)")
            result = self.algorithm.synonymize(text)
        elif mode == 'rewrite':
            logger.info("Using rewrite mode")
            result = self.rewriter.rewrite(text, rewrite_prompt)
        else:
            logger.error(f"Unknown mode: {mode}")
            return text
        
        # Optional correction pass
        if apply_correction and check_prompt and result:
            logger.info("Applying correction pass")
            result = self.corrector.correct(result, check_prompt)
        
        return result


def split_into_sentences(text: str) -> List[Dict]:
    """
    Split text into sentences
    Preserves sentence boundaries and punctuation
    """
    text = text.strip()
    if not text:
        return []
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Protect abbreviations and decimals
    text = re.sub(
        r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|Inc|Ltd|Co)\.',
        r'\1<<<ABBR>>>',
        text
    )
    text = re.sub(r'(\d+)\.(\d+)', r'\1<<<DEC>>>\2', text)
    
    # Split on sentence-ending punctuation followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    result = []
    for idx, sentence in enumerate(sentences):
        # Restore abbreviations and decimals
        sentence = sentence.replace('<<<ABBR>>>', '.')
        sentence = sentence.replace('<<<DEC>>>', '.')
        sentence = sentence.strip()
        
        if sentence:
            # Extract ending punctuation
            ending_punct = ''
            punct_match = re.search(r'([.!?]+)$', sentence)
            if punct_match:
                ending_punct = punct_match.group(1)
            
            result.append({
                'index': idx,
                'text': sentence,
                'ending_punct': ending_punct,
                'word_count': len(sentence.split())
            })
    
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AI Synonymizer - Three-Phase Text Synonymization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Synonymize text directly
  python synonymizer.py --text "The quick brown fox jumps over the lazy dog." --api-key "sk-..."
  
  # Process file with synonymization
  python synonymizer.py --file input.txt --output output.txt --api-key "sk-..."
  
  # Use rewrite mode
  python synonymizer.py --text "Your text here" --mode rewrite --api-key "sk-..."
  
  # Use custom model and enable debug
  python synonymizer.py --text "Your text" --model gpt-3.5-turbo --debug --api-key "sk-..."
  
  # Apply correction pass
  python synonymizer.py --text "Your text" --correct --api-key "sk-..."
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--text', type=str, help='Text to process')
    input_group.add_argument('--file', type=Path, help='Input file path')
    
    # Output options
    parser.add_argument('--output', '-o', type=Path, help='Output file path (default: stdout)')
    
    # API configuration
    parser.add_argument(
        '--api-key',
        type=str,
        default=os.environ.get('OPENAI_API_KEY'),
        help='OpenAI API key (or set OPENAI_API_KEY env variable)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4',
        help='OpenAI model to use (default: gpt-4)'
    )
    
    # Processing options
    parser.add_argument(
        '--mode',
        type=str,
        choices=['synonymize', 'rewrite'],
        default='synonymize',
        help='Processing mode (default: synonymize)'
    )
    parser.add_argument(
        '--correct',
        action='store_true',
        help='Apply correction pass after processing'
    )
    parser.add_argument(
        '--rewrite-prompt',
        type=str,
        help='Custom rewrite prompt'
    )
    parser.add_argument(
        '--check-prompt',
        type=str,
        help='Custom correction prompt'
    )
    
    # Advanced options
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--timeout', type=int, default=60, help='API timeout in seconds')
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        parser.error("API key is required. Use --api-key or set OPENAI_API_KEY environment variable")
    
    # Read input text
    if args.file:
        if not args.file.exists():
            logger.error(f"Input file not found: {args.file}")
            sys.exit(1)
        
        try:
            text = args.file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            sys.exit(1)
    else:
        text = args.text
    
    # Configure synonymizer
    config = SynonymizerConfig(
        api_key=args.api_key,
        model=args.model,
        mode=args.mode,
        timeout=args.timeout,
        debug=args.debug
    )
    
    # Process text
    synonymizer = Synonymizer(config)
    
    try:
        result = synonymizer.process(
            text=text,
            mode=args.mode,
            rewrite_prompt=args.rewrite_prompt,
            check_prompt=args.check_prompt,
            apply_correction=args.correct
        )
        
        # Output result
        if args.output:
            try:
                args.output.write_text(result, encoding='utf-8')
                logger.info(f"Result written to: {args.output}")
            except Exception as e:
                logger.error(f"Failed to write output file: {e}")
                sys.exit(1)
        else:
            print("\n" + "=" * 60)
            print("RESULT:")
            print("=" * 60)
            print(result)
            print("=" * 60)
    
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
