# Sequence-LLM v0.2 Specification

## Objective

Deliver a stable sequential multi-model runtime for local LLMs.

### Startup

- Model starts within configured timeout
- Health endpoint responds 200

### Switching

- Switching between models works repeatedly
- No orphan processes remain

### Streaming

- Tokens stream progressively
- Stall detection triggers clear error

### Diagnostics

- Server logs saved to ~/.seq_llm/logs
- Errors reference logfile path

### Safety

- Conversations trimmed when exceeding context
- No OOM crashes from context overflow
