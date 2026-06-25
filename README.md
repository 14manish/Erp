# Aerospace Drone Manufacturing ERP

An end-to-end Enterprise Resource Planning (ERP) implementation built on **Odoo 17 Community Edition**, specifically tailored for aerospace manufacturing and drone assembly.

This repository contains the Docker deployment configuration and custom Odoo add-ons required to run the full supply chain, manufacturing, and financial lifecycle of a drone production facility.

## Key Features Configured

*   **Advanced Manufacturing & Routing:** 
    *   2-Step Manufacturing (Pick Components -> Assemble).
    *   Bill of Materials (BOMs) with integrated SOPs and Work Center instructions (Tablet-view for factory workers).
*   **Supply Chain & Procurement:**
    *   Make-to-Order (MTO) and Reordering Rules for automated Purchasing (Requests for Quotation).
    *   Automated backorder handling for partial shipments.
*   **Aerospace Traceability & Quality:**
    *   Strict Global Lot and Serial Number tracking for both raw materials (e.g., BLDC Motors, Flight Controllers) and finished goods.
    *   Goods Receipt Note (GRN) tracking.
*   **HR & Labor Cost Tracking:**
    *   Employee Kiosk check-in via PIN.
    *   Direct integration of employee hourly labor costs into the final manufacturing valuation of the drones.
*   **Finance & Sales:**
    *   Quote-to-Cash workflow.
    *   Automated invoicing based on delivered vs ordered quantities.

## Custom Add-ons included

### `drone_traceability`
A custom Odoo Python/XML module designed to extend the core Odoo functionality for aerospace needs. 
*(Includes data models for Drone products, components, and demo data initialization).*

## Getting Started

### Prerequisites
*   Docker & Docker Compose
*   PostgreSQL (handled via Docker container)

### Installation & Execution

1. Clone this repository:
   ```bash
   git clone https://github.com/I-am-Krish/Enterprise-Resource-Planning-ERP.git
   cd Enterprise-Resource-Planning-ERP
   ```

2. Start the Odoo ERP environment:
   ```bash
   sudo docker compose up -d
   ```

3. Access the ERP interface:
   Open your browser and navigate to: `http://localhost:8069`

4. Login with your Admin credentials.

## Tech Stack
*   **Core:** Odoo 17 (Community Edition)
*   **Database:** PostgreSQL 15
*   **Custom Modules:** Python 3, XML, Odoo ORM
*   **Deployment:** Docker Compose
