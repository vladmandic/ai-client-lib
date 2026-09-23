# Notes

## Schema

Each provider/model has its own input and output schema
I've tried to unify output schema parsing, but its fragile
Input schema is strictly per provider/model as fields vastly differ

## Images

Input image handling is also messy as depending on provider/model, it may be a list or single entity and that entity may be a data-uri, id-provider-upload or external url.

## Workflows

All providers accept both synchronous (blocking/waiting for result) and asynchronous (non-blocking) requests (using webhooks/callbacks) except:
- BytePlus is sync for images and async for video
- PixVerse is sync-only

## Content Filters

BytePlus content filters are extremely strict and may block content that other providers allow.
