"""Support for the Aldes sensors."""
from __future__ import annotations
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
    EntityCategory,
    UnitOfPower,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FRIENDLY_NAMES
from .entity import AldesEntity

from collections.abc import Callable
from dataclasses import dataclass

ATTR_HUMIDITY = "humidity"
ATTR_TEMPERATURE = "temperature"
ATTR_CO2 = "CO2"
ATTR_QAI = "Air Quality Index"
ATTR_POLLUANT = "Polluant Dominant"
ATTR_VARHR = "Humidity Variation"
ATTR_PWRQAI = "Actual mode"


@dataclass
class AldesSensorDescription(SensorEntityDescription):
    """A class that describes sensor entities."""

    attributes: tuple = ()
    keys: list[str] = None
    value: Callable = None
    path1: str = None
    path2: str = None
    path3: str = None
    divisor: int = None


EASY_HOME_SENSORS = {
    f"Kitchen_{ATTR_HUMIDITY}": AldesSensorDescription(
        key="status",
        icon="mdi:water-percent",
        name="Kitchen Humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="HrCuCo",
    ),
    f"Kitchen_{ATTR_TEMPERATURE}": AldesSensorDescription(
        key="status",
        icon="mdi:thermometer",
        name="Kitchen Temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="TmpCu",
        divisor=10,
    ),
    f"Bathroom_1_{ATTR_HUMIDITY}": AldesSensorDescription(
        key="status",
        icon="mdi:water-percent",
        name="Bathroom 1 Humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="HrBa1Co",
    ),
    f"Bathroom_1_{ATTR_TEMPERATURE}": AldesSensorDescription(
        key="status",
        icon="mdi:thermometer",
        name="Bathroom 1 Temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="TmpBa1",
        divisor=10,
    ),
    f"Bathroom_2_{ATTR_HUMIDITY}": AldesSensorDescription(
        key="status",
        icon="mdi:water-percent",
        name="Bathroom 2 Humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="HrBa2Co",
    ),
    f"Bathroom_2_{ATTR_TEMPERATURE}": AldesSensorDescription(
        key="status",
        icon="mdi:thermometer",
        name="Bathroom 2 Temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="TmpBa2",
        divisor=10,
    ),
    f"{ATTR_CO2}": AldesSensorDescription(
        key="status",
        icon="mdi:molecule-co2",
        name="Carbon dioxyde",
        translation_key="co2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="CO2",
    ),
    f"{ATTR_QAI}": AldesSensorDescription(
        key="status",
        icon="mdi:air-filter",
        name="Air Quality Index",
        translation_key="qai",
        device_class=SensorDeviceClass.AQI,
        native_unit_of_measurement=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="Qai",
        path3="actualValue",
    ),
    f"{ATTR_POLLUANT}": AldesSensorDescription(
        key="status",
        icon="mdi:flower-pollen",
        name="Polluant Dominant",
        translation_key="qai",
        native_unit_of_measurement=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="Qai",
        path3="polluantDominant",
    ),
    f"{ATTR_VARHR}": AldesSensorDescription(
        key="status",
        icon="mdi:cloud-percent",
        name="Humidity Variation",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="VarHR",
    ),
    f"{ATTR_PWRQAI}": AldesSensorDescription(
        key="status",
        icon="mdi:wind-power",
        name="Current Mode",
        translation_key="mode",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        path1="indicator",
        path2="VarHR",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Aldes sensors from a config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AldesSensorEntity] = []
    sensors = EASY_HOME_SENSORS
    for product in coordinator.data:
        for sensor, description in sensors.items():
            entities.append(
                AldesSensorEntity(
                    coordinator,
                    entry,
                    product["serial_number"],
                    product["reference"],
                    product["modem"],
                    sensor,
                    description,
                )
            )

    async_add_entities(entities)


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
        description,
    ) -> None:
        super().__init__(
            coordinator, config_entry, product_serial_number, reference, modem
        )
        self.probe_id = probe_id
        self.entity_description = description
        self._attr_native_value = self._determine_native_value()

    # @property
    # def device_info(self):
    #    """Return the device info."""
    #    return DeviceInfo(
    #        identifiers={(DOMAIN, self.product_serial_number)},
    #        name=f"{FRIENDLY_NAMES[self.reference]} {self.product_serial_number}",
    #        model=FRIENDLY_NAMES[self.reference],
    #    )

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        # return f"{DOMAIN}_{self.product_serial_number}_{self.entity_description.name}"
        return f"{FRIENDLY_NAMES[self.reference]}_{self.product_serial_number}_{self.entity_description.name}"

    @property
    def name(self):
        """Return a name to use for this entity."""
        for product in self.coordinator.data:
            if product["serial_number"] == self.product_serial_number:
                return f"{FRIENDLY_NAMES[self.reference]} {self.product_serial_number} {self.entity_description.name}"
            return None

    def _determine_native_value(self):
        """Determine native value."""
        for product in self.coordinator.data:
            if product["isConnected"]:
                if product["serial_number"] == self.product_serial_number:
                    if self.entity_description.path3 is None:
                        value = product[self.entity_description.path1][
                            self.entity_description.path2
                        ]
                    else:
                        value = product[self.entity_description.path1][
                            self.entity_description.path2
                        ][self.entity_description.path3]
                    if self.entity_description.divisor is None:
                        return value
                    else:
                        return value / self.entity_description.divisor
                else:
                    return None
            else:
                return None

    @callback
    def _handle_coordinator_update(self):
        """Fetch state from the device."""
        native_value = self._determine_native_value()
        # Sometimes (quite rarely) the device returns None as the sensor value so we
        # check that the value: before updating the state.
        if native_value is not None:
            self._attr_native_value = native_value
            super()._handle_coordinator_update()
