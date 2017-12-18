# RealEstateTW
Analyze Real Estate Actual Price Registration open-sourced by the MOI (Ministry of the Interior)

### Installation
1. Ensure Python3 is installed:
> ```bash
> brew install python3
> ```

2. Crawl Actual Price datasets by issuing the following command:
> ```bash
> python3 crawler.py
> ```

3. Initialize database by issuing the following:
> ```bash
> python3 db_creator.py
> ```

4. Geocode Taiwanese addresses into GPS coordinates for further analysis:
> ```bash
> python3 address_geocoder.py
> ```

5. Issue the following command to start model training:
> ```bash
> python3 model.py
> ```