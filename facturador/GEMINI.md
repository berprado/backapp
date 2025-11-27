# BACKINVOICE - Electronic Invoicing System

## Project Overview

**BACKINVOICE** is a Python-based electronic invoicing system designed for the Bolivian tax system (SIN - Servicio de Impuestos Nacionales). It is built using **Streamlit** as the primary UI framework and handles both online and offline (contingency) billing scenarios.

The system integrates with SIAT (Sistema de Facturación en Línea) via SOAP services to validate invoices, manage events, and handle anulacion/reversion processes.

## Key Features

*   **Streamlit UI:** Interactive web-based interface for issuing invoices and managing system state.
*   **SIAT Integration:** Robust SOAP client (`siat_service_client.py`) for communicating with SIN servers.
*   **Offline/Contingency Mode:** Automatically detects connection loss and switches to offline mode, allowing continued billing with subsequent synchronization.
*   **PDF Generation:** Generates invoice PDFs (`pdfs/` directory) and handles thermal printing.
*   **XML Signing & Validation:** Generates and signs XML documents (`xmls/` directory) compliant with SIN standards.

## Architecture & Directory Structure

*   **`main.py`**: The application entry point. Handles the main Streamlit lifecycle, connection checks, and UI rendering.
*   **`config.py`**: Basic project configuration and path definitions.
*   **`siat_service_client.py`**: Centralized client for all SIAT SOAP interactions.
*   **`business_logic.py` / `invoice_manager.py`**: Core business logic for processing invoices.
*   **`data_access.py` / `database.py`**: Database interaction layer.
*   **`communication_manager.py`**: Manages network connectivity checks and diagnostic logic.
*   **`print_manager.py`**: Background worker for handling print jobs.
*   **Directories:**
    *   `pdfs/`: Stores generated invoice PDFs.
    *   `xmls/`: Stores generated and signed invoice XMLs.
    *   `.streamlit/`: Streamlit configuration.

## Setup & Usage

### Prerequisites
*   Python 3.x
*   Recommended: Virtual environment

### Installation
(Inferred dependencies based on imports)
```bash
pip install streamlit requests python-dotenv fonttools matplotlib pillow urllib3
```

### Configuration
The system relies on environment variables for SIAT credentials. Ensure a `.env` file is present in the root directory with the following keys:
*   `CODIGO_AMBIENTE`
*   `CODIGO_SISTEMA`
*   `CODIGO_SUCURSAL`
*   `NIT`
*   `CUIS`
*   `API_KEY`
*   (And other SIAT-specific codes)

### Running the Application
To start the application, run:
```bash
streamlit run main.py
```

## Development Guidelines

*   **Logging:** Uses a custom logger (`logger_config.py`). Avoid standard `print` statements; use `logger.info()`, `logger.error()`, etc.
*   **UI Components:** New UI features should be modularized in `ui_copy.py` or separate tab modules (`tabs/`).
*   **SIAT Interaction:** All new interactions with SIN services must go through `siat_service_client.py` to maintain consistency.
*   **Error Handling:** The system uses extensive error handling to ensure stability during network fluctuations. Ensure new features handle offline states gracefully.
