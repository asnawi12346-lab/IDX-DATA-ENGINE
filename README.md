# IDX-DATA-ENGINE

Indonesia Stock Exchange data acquisition and validation engine.

## Goals

- Collect official IDX market data
- Support historical data acquisition
- Support incremental daily updates
- Validate data quality and schema
- Store normalized market data
- Provide a reliable data layer for UMAR_AI_PRO

## Development Strategy

1. Windows native development
2. Test one stock
3. Test 21 focus stocks
4. Test the broader Indonesian stock universe
5. Historical backfill
6. Incremental updates
7. Stress testing
8. Docker deployment only after native stability

## Important

This project is currently a data-engineering project.

The UMAR_AI_PRO machine-learning pipeline will not be modified during the initial data-engineering phase.
