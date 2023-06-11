"""Support for the Aldes sensors."""
from __future__ import annotations
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, FRIENDLY_NAMES
from .entity import AldesEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Aldes sensors from a config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[AldesSensorEntity] = []

    for product in coordinator.data:
        for probe_id in product["indicator"]:
            if "Tmp" in probe_id:
                sensors.append(
                    AldesSensorEntity(
                        coordinator,
                        entry,
                        product["serial_number"],
                        product["reference"],
                        product["modem"],
                        probe_id,
                        "temperature",
                        UnitOfTemperature.CELSIUS,
                    )
                )
            elif "Hr" in probe_id and "Co" in probe_id:
                sensors.append(
                    AldesSensorEntity(
                        coordinator,
                        entry,
                        product["serial_number"],
                        product["reference"],
                        product["modem"],
                        probe_id,
                        "humidity",
                        PERCENTAGE,
                    )
                )
            # CO2 and QAI has to be moved in Air Quality platform
            elif probe_id == "CO2":
                sensors.append(
                    AldesSensorEntity(
                        coordinator,
                        entry,
                        product["serial_number"],
                        product["reference"],
                        product["modem"],
                        probe_id,
                        "carbon_dioxide",
                        CONCENTRATION_PARTS_PER_MILLION,
                    )
                )
            elif probe_id == "Qai":
                sensors.append(
                    AldesSensorEntity(
                        coordinator,
                        entry,
                        product["serial_number"],
                        product["reference"],
                        product["modem"],
                        probe_id,
                        "air_quality_index",
                        PERCENTAGE,
                    )
                )
            elif probe_id == "thermostats":
                sensors.append(
                    AldesSensorEntity(
                        coordinator,
                        entry,
                        product["serial_number"],
                        product["reference"],
                        product["modem"],
                        probe_id["ThermostatId"],
                        "temperature",
                        UnitOfTemperature.CELSIUS,
                    )
                )

    async_add_entities(sensors)


class AldesSensorEntity(AldesEntity, SensorEntity):
    """Define an Aldes sensor."""

    def __init__(
        self,
        coordinator,
        config_entry,
        product_serial_number,
        reference,
        modem,
        probe_id,
        probe_type,
        probe_unit,
    ) -> None:
        super().__init__(
            coordinator, config_entry, product_serial_number, reference, modem
        )
        self.probe_id = probe_id
        self._attr_device_class = probe_type
        self._attr_native_unit_of_measurement = probe_unit

    @property
    def device_info(self):
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.product_serial_number)},
            name=f"{FRIENDLY_NAMES[self.reference]} {self.product_serial_number}",
            model=FRIENDLY_NAMES[self.reference],
        )

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{DOMAIN}_{self.product_serial_number}_{self.probe_id}"

    @property
    def name(self):
        """Return a name to use for this entity."""
        for product in self.coordinator.data:
            if product["serial_number"] == self.product_serial_number:
                for probe_id in product["indicator"]:
                    if probe_id == self.probe_id:
                        return f"{FRIENDLY_NAMES[self.reference]} {self.product_serial_number} {probe_id}"
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update attributes when the coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Update binary sensor attributes."""
        for product in self.coordinator.data:
            if product["isConnected"]:
                if product["serial_number"] == self.product_serial_number:
                    for probe_id in product["indicator"]:
                        if probe_id == "thermostats":
                            for thermostat in product["indicator"]["thermostats"]:
                                if thermostat["ThermostatId"] == self.probe_id:
                                    self._attr_native_value = round(
                                        thermostat["CurrentTemperature"], 1
                                    )
                        elif probe_id == self.probe_id:
                            if (
                                self._attr_device_class == "temperature"
                                and "Tmp" in probe_id
                            ):
                                self._attr_native_value = (
                                    product["indicator"][probe_id] / 10
                                )
                            elif self._attr_device_class == "air_quality_index":
                                self._attr_native_value = product["indicator"][
                                    probe_id
                                ]["actualValue"]
                            else:
                                self._attr_native_value = product["indicator"][probe_id]
            else:
                self._attr_native_value = None
