# Changelog

All notable changes to Saraswathi Agent will be documented in this file.

## [0.8.4] - 2025-01-16

### Added

- Added /healthz in `main.py` for pod health check

## [0.8.3] - 2024-11-30

### Fixed

- Fixed test_chart_feedback qdrant mock error

## [0.8.2] - 2024-11-29

### Changed

- Changed the run testcase code to accomodate latest streaming code for testing purposes

## [0.8.1] - 2024-11-29

### Fixed

- Fixed logger in logging library for connection rollback

## [0.8.0] - 2024-11-29

### Fixed

- Fixed logging library code standard

### Added

- Added error logging for each error
- Added performance logging for each module

### Changed

- Changed Qdrant collection namespaces for table and column levels from RADAR data to 27 KPI Cross-Selling Banking Data.

## [0.7.2] - 2024-11-26

### Added

- Added unit test for general SQL query generator and executor.

### Changed

- Changed Qdrant collection namespaces for table and column levels from 27 KPI Cross-Selling Banking Data to RADAR Data.

## [0.7.1] - 2024-11-25

### Added

- Added general SQL query API
- Added question answering API

### Changed

- Changed Chroma DB to Qdrant

## [0.7.0] - 2024-11-20

### Added

- Added dynamic sql samples to all sql libraries in sql generator

## [0.6.0] - 2024-11-19

### Added

- Added dynamic sql samples in sql generator

## [0.5.2] - 2024-11-19

### Added

- Added unit test for calculate token usage.

## [0.5.1] - 2024-11-18

### Added

- Added input_tokens and output_tokens to the logging of Chart LLM calls.

### Fixed

- Fixed the automatic module creation in MongoDB by retrieving predefined module information from the .env file.
- Fixed unit tests for the Logging Chart LLM Calls API and automatic module creation functions in unit_test_logging.py.

## [0.5.0] - 2024-11-15

### Added

- Added dynamic axis samples in axis generator

## [0.4.0] - 2024-11-15

### Added

- Added feedback querying API based on question
- Added feedback querying API based on user query

## [0.3.3] - 2024-11-14

### Added

- Added unit tests for Logging Chart LLM Calls API and automatic module creation functions in unit_test_logging.py.
- Added comments for documentation in modules.py.

## [0.3.2] - 2024-11-12

### Added

- Added automatic MongoDB creation for module, chart LLM call, and chart.
- Added automatic module creation in MongoDB on first run of main.py if not existing.
- Added module ID in .env for configuration.

## [0.3.1] - 2024-11-12

### Changed

- Changed chart feedback save input from str to dict
- Changed question samples local json path from static to dynamic path

### Fixed

- Fixed chart id in chart logging from question generator

## [0.3.0] - 2024-11-12

### Added

- Added dynamic question samples in question generator
- Added question module logging

### Fixed

- Removed duplicate adjust chart title function in extractor
- Removed unused column metadata querying

## [0.2.0] - 2024-11-11

### Added

- Added chart LLM calls logging
- Added feedback save API
- Added feedback load API

### Removed

- Removed non-D3 chart functions

## [0.1.2] - 2024-11-10

### Added

- Added sql query checker for non-numerical columns in histogram chart
- Added updater function for d3 library charts
- Added streaming dummy api version 40
- Added tools for database migration
- Added chart limitation to maximum 6 charts
- Added descriptions, conditions and fallbacks for each chart type in question generator

### Fixed

- Fixed bubbleplot summarizer
- Fixed generated beautiful table by adding user query
- Fixed missing `zAxis` key in bubbleplot chart
- Fixed updater based on extractor fixes
- Fixed 1000 pages in line chart x-axis
- Fixed scatterplot and bubbleplot description prompt overflow in question generator
- Fixed question generator to select suitable chart type based on columns data tribe required

### Changed

- Changed LLM sorting refactored
- Changed table and column level namespace to devtest4
- Changed extractor refactored

## [0.1.1] - 2024-10-29

### Fixed

- Fixed bubbleplot overflow in insight generator using summarized bubbleplot data template
- Fixed non-numerical column in histogram chart, bubbleplot chart, and scatterplot chart
- Fixed generate data asset API due to missing user query
- Fixed Missing 'zAxis' key in bubbleplot chart
- Fixed zAxis rename in aggregated table for bubbleplot chart
