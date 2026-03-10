# Pollenvarsel Integration

A custom Home Assistant integration for displaying Norwegian pollen forecasts from NAAF (Norwegian Asthma and Allergy Association) for multiple locations.

## Installation

### Via HACS (Recommended)
1. Go to HACS > Integrations
2. Click the menu (⋮) and select "Custom repositories"
3. Add `https://github.com/kahera/pollenvarsling` as a Custom Repository
4. Select the category "Integration"
5. Search for "Pollenvarsel" and install

### Manual
Copy the `custom_components/pollen_naaf_yr` folder to your `custom_components` directory in Home Assistant.

## Configuration

Add this to your `configuration.yaml`:

```yaml
pollenvarsel_naaf_yr:
  pollen_types:
    - hazel # Hassel
    - alder # Or
    - willow # Salix ℹ️: id needs verification when pollen season begins
    - birch # Bjørk ℹ️: id needs verification when pollen season begins
    - grass # Gress ℹ️: id needs verification when pollen season begins
    - mugwort # Burot ℹ️: id needs verification when pollen season begins
  locations:
    - location_id: "1-189277"
      location_name: "Molde" # Optional
    - location_id: "1-92416"
  language: nb # Optional (default: nb)
  update_frequency: 1 # Hours (optional, default: 3)
```

### Configuration Options

- **pollen_types** (required): List of pollen types to track (language-independent IDs). Available types:
  `hazel`, `alder`, `willow`, `birch`, `grass`, `mugwort`

- **locations** (required): List of locations to monitor
  - **location_id** (required): YR location ID (found in the API URL)
  - **location_name** (optional): Your custom name for the location

  >  ℹ️: Only locations in mainland Norway will work.

- **language** (optional): Language for pollen type names and distribution levels. Default: `nb`
  - `nb` - Norwegian bokmål
  - `nn` - Norwegian nynorsk
  - `sme` - Northern Sami
  - `en` - English

- **update_frequency** (optional): How often to fetch data, in hours. Default: `3`

## Finding Location IDs

Visit https://www.yr.no/nb and search for your location. The location ID is in the response URL, where the ID is located after `daglig-tabell` as such: 
`https://www.yr.no/nb/værvarsel/daglig-tabell/{locationID}/Norge/{otherNonRelevantLocationInfo}`
> Example: 
>
> `https://www.yr.no/nb/værvarsel/daglig-tabell/1-189277/Norge/M%C3%B8re%20og%20Romsdal/Molde/Molde`
> where `1-189277` is the ID. 


## Sensors Created
For each pollen type and location, the integration creates two sensors:
- `sensor.pollen_{pollen_type}_{location_name}_today` or `sensor.pollen_{pollen_type}_{region_name}_today`
- `sensor.pollen_{pollen_type}_{location_name}_tomorrow` or `sensor.pollen_{pollen_type}_{region_name}_tomorrow`

### Sensor States
- `none` - Pollen type not forecast for that day
- `low` - Low pollen level
- `moderate` - Moderate pollen level
- `high` - High pollen level
- `extreme` - Extreme pollen level

### Sensor Attributes
- `pollen_name` - Localized name of the pollen type (e.g., "Hassel" in nb, "Hazel" in en)
- `level_name` - Localized distribution level name (e.g., "Beskjeden", "Moderat")
- `date` - Forecast date
- `region_name` - Region name fetched from the API
- `location_name` - Custom name as set in the configuration, if present
- `last_updated` - Date & time for when the sensor was last updated

## Automation Example

```yaml
automation:
  - alias: "High Pollen Alert"
    trigger:
      - platform: state
        entity_id: sensor.pollen_birch_molde_today
        to: "high"
      - platform: state
        entity_id: sensor.pollen_birch_molde_today
        to: "extreme"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "High birch pollen today!"
```

## Update Interval

Data is fetched every 3 hours by default. To customize, add the `update_frequency`

## Troubleshooting

If sensors don't appear:
1. Restart Home Assistant
2. Check that location IDs are correct
3. Verify pollen type IDs are correct (use the language-independent IDs: `hazel`, `alder`, `willow`, `birch` `grass`, `mugwort`)
4. Check Home Assistant logs for errors
