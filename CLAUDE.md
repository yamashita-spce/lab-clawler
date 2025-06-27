# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web crawler system designed for IoT device web interface scanning and security analysis. The project focuses on crawling complex web applications with framesets, JavaScript, and authentication mechanisms typically found in IoT device management interfaces.

## Core Architecture

The project consists of two main crawler systems:

### Legacy Crawlers (legacy_crawlers/)
1. **simple_crawler.py** - Basic HTTP-based crawler using requests library for simple web pages
2. **authentication_crawler.py** - Advanced Selenium-based crawler with authentication capabilities and frameset handling  
3. **new_web_get.py** - Selenium crawler focused on frame endpoint discovery and HTML collection

### Next-Gen IoT Crawler (nextgen_crawler/)
1. **iot_crawler/config.py** - Configuration management and environment variable handling
2. **iot_crawler/authentication.py** - Universal IoT device authentication system
3. **iot_crawler/page_crawler.py** - Comprehensive page crawling with frame support
4. **iot_crawler/session_manager.py** - Session state management for reproducibility
5. **iot_crawler/structure_analyzer.py** - DOM, URL, and security analysis
6. **iot_crawler/output_manager.py** - Multi-format output generation
7. **iot_crawler/main_crawler.py** - Main orchestrator integrating all components
8. **iot_crawler_cli.py** - Command-line interface

### Key Components (Next-Gen)

- **IoTMainCrawler class** (nextgen_crawler/iot_crawler/main_crawler.py): Main crawler orchestrator with WebDriver management, authentication flow, and comprehensive analysis
- **Frame processing system**: Advanced frameset handling with dynamic JavaScript execution and DOM updates
- **Authentication system**: Universal IoT device authentication with multiple selector patterns and frame-aware processing
- **Session management**: Complete session state capture and restoration for fuzzing reproducibility
- **Security analysis**: Automated vulnerability detection and attack surface analysis
- **Output system**: Multi-format output with HTML, JSON, fuzzing data, and session files

## Development Commands

### Environment Setup
```bash
# Legacy crawlers
cd legacy_crawlers
pip install -r requirements_legacy.txt

# Next-gen crawler (recommended)
cd nextgen_crawler
pip install -r requirements_nextgen.txt

# Ensure ChromeDriver is installed and in PATH for Selenium functionality
```

### Running Legacy Crawlers
```bash
cd legacy_crawlers

# Simple crawler for basic pages
python simple_crawler.py [URL] [-o output_dir]

# Authentication crawler with frame processing
python authentication_crawler.py [URL] [-o output_dir] [-w wait_seconds]

# Authentication crawler with login
python authentication_crawler.py [URL] --login [--username USER] [--password PASS]

# Frame endpoint discovery
python new_web_get.py [URL] [-w wait_seconds] [-o output_dir]
```

### Running Next-Gen Crawler (Recommended)
```bash
cd nextgen_crawler

# Basic crawl
python iot_crawler_cli.py crawl --url http://192.168.1.1 --user admin --pass password

# Verbose crawl with analysis
python iot_crawler_cli.py --verbose crawl --url http://127.0.0.1:8888 --user admin --pass password

# Session restoration
python iot_crawler_cli.py restore --session-file ./sessions/session_abc123.json

# Status check
python iot_crawler_cli.py status
```

### Output Structure
#### Legacy Crawlers
- `legacy_crawlers/crawl_output/` - Simple crawler results
- `legacy_crawlers/crawl_output/auth_html/` - Authentication crawler frame HTML files
- `legacy_crawlers/frames_html/` - Frame endpoint discovery results

#### Next-Gen Crawler
- `nextgen_crawler/iot_crawler_output/html/` - Raw HTML pages
- `nextgen_crawler/iot_crawler_output/frames/` - Frame content
- `nextgen_crawler/iot_crawler_output/json/` - Structured crawl data
- `nextgen_crawler/iot_crawler_output/analysis/` - Security analysis
- `nextgen_crawler/iot_crawler_output/fuzzing/` - Fuzzing preparation data
- `nextgen_crawler/iot_crawler_output/sessions/` - Session reproduction data
- `nextgen_crawler/iot_crawler_output/logs/` - Execution logs

## Key Technical Details

### Frame Processing
The authentication crawler implements sophisticated frame handling:
- Dynamic frame detection and switching using Selenium
- Frame source URL waiting mechanism with timeout handling
- DOM change adaptation through element re-acquisition
- Sequential frame processing with proper context switching

### Authentication Flow
Located in authentication_crawler.py:194-341:
- Supports frameset-based login interfaces (targets "master" frame)
- Handles modal overlay removal via JavaScript injection
- Implements multiple success verification strategies
- Configurable username/password with defaults (admin/password)

### Error Handling
- WebDriver initialization failure graceful handling
- Frame switching exception management
- Timeout handling for page loads and element waits
- DOM element state change resilience

## File Naming Conventions
- URL-based filename sanitization replaces special characters with underscores
- Frame files include index suffixes for uniqueness
- Output files use UTF-8 encoding for international character support

## Testing and Validation
- Manual testing against localhost:8888 (based on examples in README)
- Frame content validation through HTML tag presence checking
- Authentication success verification through element visibility/invisibility checks