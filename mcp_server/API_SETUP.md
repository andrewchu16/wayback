# MCP Server API Setup Guide

This guide explains how to set up API credentials for the MCP server providers.

## Overview

The MCP server supports multiple transportation providers. **All APIs are optional** - if credentials are not provided, the server will use mock data based on distance calculations.

## Available APIs

### Google Maps API (for Transit)
- Optional - used for transit route planning
- Get API key from: https://console.cloud.google.com/
- Set: `GOOGLE_MAPS_API_KEY=your_key`

### OpenRouteService (ORS)
- Optional - alternative transit/route planning
- Get API key from: https://openrouteservice.org/
- Set: `ORS_API_KEY=your_key`

### Lime GBFS
- **Public API** - no credentials needed
- Default URL already configured for San Francisco
- Can override with: `LIME_GBFS_URL=your_url`

## Mock Mode

If no credentials are provided, the server will:
- Calculate estimates based on distance
- Use reasonable defaults for pricing and duration
- Still return valid responses for development/testing

This allows you to develop and test without API credentials.

## Security Best Practices

1. **Never commit `.env` files**
   - The `.gitignore` already excludes `.env`
   - Use `env.example` as a template (copy it to `.env`)

2. **Use environment variables**
   - Never hardcode credentials in code
   - Use `.env` for local development
   - Use secure vaults for production (AWS Secrets Manager, etc.)

3. **Rotate credentials regularly**
   - Change your API keys periodically
   - Revoke old keys if compromised

4. **Limit API access**
   - Only grant necessary scopes
   - Monitor API usage in provider dashboards

## Testing Without Credentials

You can test the MCP server without any credentials:
- Mock data will be returned for all providers
- Responses will include realistic estimates based on distance
- Perfect for development and local testing

To test with real APIs:
1. Get credentials from provider
2. Add them to `.env` file
3. Restart the MCP server
4. Real API responses will be used instead of mocks

