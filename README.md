# AI Synonymizer - Three-Phase Text Synonymization

A standalone Python script that implements intelligent text synonymization using OpenAI's API. Based on a three-phase algorithm that extracts, synonymizes, and substitutes words while preserving meaning and structure.

## Features

- **Three-Phase Algorithm**: Efficient synonymization with exactly 3 API calls per text
  - Phase 1: Extract adjectives and meaningful verbs
  - Phase 2: Generate 1:1 synonym mapping
  - Phase 3: Apply substitutions intelligently
  
- **Multiple Modes**:
  - `synonymize`: Three-phase algorithm (default)
  - `rewrite`: AI-powered text rewriting
  
- **Smart Extraction**: Excludes named entities, preserves proper nouns
- **Context-Aware**: Generates synonyms that fit naturally in context
- **Batch Processing**: Efficient API usage
- **Optional Correction Pass**: Additional quality check

## Installation

### Requirements

- Python 3.7 or higher
- OpenAI API key

### Install Dependencies

```bash
pip install requests
```

Or using the requirements file:

```bash
pip install -r requirements_synonymizer.txt
```

## Usage

### Basic Usage

```bash
# Set your API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Synonymize text directly
python synonymizer.py --text "The recent report indicated significant growth in the market."

# Process a file
python synonymizer.py --file input.txt --output output.txt
```

### Advanced Usage

```bash
# Use rewrite mode
python synonymizer.py --text "Your text here" --mode rewrite

# Use a different model
python synonymizer.py --text "Your text" --model gpt-3.5-turbo

# Apply correction pass
python synonymizer.py --text "Your text" --correct

# Enable debug mode for detailed logging
python synonymizer.py --text "Your text" --debug

# Specify API key directly
python synonymizer.py --text "Your text" --api-key "sk-..."

# Custom prompts
python synonymizer.py --text "Your text" \
  --rewrite-prompt "Rewrite professionally" \
  --check-prompt "Fix grammar errors"
```

## Command-Line Arguments

### Input Options (required, choose one)
- `--text TEXT`: Text to process directly
- `--file PATH`: Input file path

### Output Options
- `--output PATH`, `-o PATH`: Output file path (default: stdout)

### API Configuration
- `--api-key KEY`: OpenAI API key (or set `OPENAI_API_KEY` env variable)
- `--model MODEL`: OpenAI model to use (default: `gpt-4`)

### Processing Options
- `--mode MODE`: Processing mode - `synonymize` or `rewrite` (default: `synonymize`)
- `--correct`: Apply correction pass after processing
- `--rewrite-prompt TEXT`: Custom rewrite prompt
- `--check-prompt TEXT`: Custom correction prompt

### Advanced Options
- `--debug`: Enable debug output
- `--timeout SECONDS`: API timeout in seconds (default: 60)

## How It Works

### Three-Phase Algorithm

The synonymizer uses a sophisticated three-phase approach:

#### Phase 1: Extract
Analyzes the text to identify:
- All adjectives (excluding those in proper names)
- All verbs (including auxiliaries, participles)
- Action nouns (discrete events/actions)

**Excludes**:
- Named entities (people, companies, places)
- Regular nouns
- Articles, prepositions, conjunctions
- Numbers and dates

#### Phase 2: Synonymize
- Generates one synonym per extracted word
- Maintains 1:1 mapping with original words
- Ensures grammatical form matches (tense, number)
- Context-aware synonym selection

#### Phase 3: Substitute
- LLM performs intelligent substitution
- Preserves punctuation and capitalization
- Maintains sentence structure
- Returns polished result

### Example

**Input:**
```
The recent report indicated significant growth in the market.
```

**Phase 1 Extraction:**
```
recent, indicated, significant, growth
```

**Phase 2 Synonyms:**
```
latest, showed, substantial, expansion
```

**Phase 3 Result:**
```
The latest report showed substantial expansion in the market.
```

## API Usage

The script makes efficient use of the OpenAI API:

- **Synonymize mode**: Exactly 3 API calls per text
- **Rewrite mode**: 1 API call per text
- **With correction**: +1 additional API call

## Configuration

### Environment Variables

```bash
# Set API key
export OPENAI_API_KEY="sk-your-key-here"

# Optional: set default model
export OPENAI_MODEL="gpt-4"
```

### Python Configuration

You can also use the script as a library:

```python
from synonymizer import Synonymizer, SynonymizerConfig

# Create configuration
config = SynonymizerConfig(
    api_key="sk-your-key",
    model="gpt-4",
    mode="synonymize",
    debug=True
)

# Create synonymizer
synonymizer = Synonymizer(config)

# Process text
result = synonymizer.process(
    text="Your text here",
    apply_correction=True
)

print(result)
```

## Examples

### Example 1: Basic Synonymization
```bash
python synonymizer.py --text "The company announced major changes to its business strategy."
```

Output:
```
The company revealed significant modifications to its business strategy.
```

### Example 2: File Processing
```bash
# Create input file
echo "The recent developments have caused significant disruption." > input.txt

# Process
python synonymizer.py --file input.txt --output output.txt

# View result
cat output.txt
```

### Example 3: Rewrite Mode
```bash
python synonymizer.py \
  --text "The study showed good results with high accuracy." \
  --mode rewrite \
  --correct
```

## Error Handling

The script includes robust error handling:
- API failures: Returns original text
- Network errors: Logs error and exits gracefully
- Invalid responses: Falls back to originals
- Keyboard interrupt: Clean exit

## Logging

- `INFO`: Standard operation progress
- `WARNING`: Non-critical issues (e.g., API response mismatches)
- `ERROR`: Critical failures

Enable debug logging with `--debug` for detailed information:
- Input text analysis
- API requests and responses
- Word extraction details
- Synonym mappings
- Substitution results

## Limitations

- Requires OpenAI API access (costs apply)
- Processing time depends on API response time
- Quality depends on model capabilities
- Best results with GPT-4 or newer models

## Troubleshooting

### "requests module not found"
```bash
pip install requests
```

### "API key is required"
```bash
# Set environment variable
export OPENAI_API_KEY="sk-your-key"

# Or use --api-key argument
python synonymizer.py --text "..." --api-key "sk-your-key"
```

### "API error: HTTP 401"
- Check that your API key is correct
- Verify API key has proper permissions

### "API error: HTTP 429"
- Rate limit exceeded
- Wait and retry
- Consider upgrading API plan

### Poor quality results
- Try using `--model gpt-4` for better results
- Enable correction pass with `--correct`
- Use debug mode to inspect extraction

## Comparison with Original PHP Script

This Python implementation provides:
- ✅ Full three-phase algorithm implementation
- ✅ All three modes (synonymize, rewrite, full)
- ✅ Sentence splitting functionality
- ✅ Correction pass support
- ✅ Debug logging
- ✅ Command-line interface
- ✅ File I/O support
- ✅ Configurable parameters
- ✅ Library usage support
- ✅ Better error handling

## License

This script is provided as-is for use in computational linguistics research.

## Support

For issues or questions, check the debug output with `--debug` flag.

## Version

Version: 1.0.0
Based on: ai-paraphraser.php (Three-Phase Synonymization Algorithm)
