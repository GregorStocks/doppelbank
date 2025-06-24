# Test Data Organization

This directory contains organized test data files for the doppelbank project.

## Directory Structure

### `bedrock/`
Contains bedrock-format test data (financial events before transformation):
- `bedrock.json` - Sample bedrock events
- `test_ledger.json` - Test ledger in bedrock format

### `detritus/`
Contains detritus-format test data (transformed bank events):
- `detritus.json` - Sample detritus events  
- `test_ledger_detritus.json` - Test ledger in detritus format

## Usage

Tests should reference data from these organized directories:
- Use `data/bedrock/` for input data to transformation tests
- Use `data/detritus/` for API and integration tests
- Copy files to appropriate runtime locations (e.g., veneer data directory) during tests

## File Formats

- **Bedrock format**: Raw financial events (card swipes, paychecks, transfers)
- **Detritus format**: Transformed bank events (addPending, addCleared, etc.)