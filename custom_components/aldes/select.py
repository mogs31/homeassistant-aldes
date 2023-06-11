"""Support for the Aldes selects."""
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN, FRIENDLY_NAMES, MODES_TEXT, TEXT_MODES
from .entity import AldesEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Aldes slects from a config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    selects: list[AldesSelectEntity] = []

    for product in coordinator.data:
        for data_line in product["indicators"][0:]:
            if data_line["type"] == "MODE":
                selects.append(
                    AldesSelectEntity(
                        coordinator,
                        entry,
                        product["serial_number"],
                        product["reference"],
                        product["modem"],
                        MODES_TEXT[data_line["value"]],
                    )
                )

    async_add_entities(selects)


class AldesSelectEntity(AldesEntity, SelectEntity):
    """Define an Aldes select."""

    def __init__(
        self,
        coordinator,
        config_entry,
        product_serial_number,
        reference,
        modem,
        mode,
    ) -> None:
        super().__init__(
            coordinator, config_entry, product_serial_number, reference, modem
        )
        self._attr_icon = "mdi:tune"
        self._attr_device_class = EntityCategory.CONFIG
        self._attr_native_unit_of_measurement = None
        self._attr_options = list(TEXT_MODES.keys())
        self._mode = mode

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
        return f"{DOMAIN}_{self.product_serial_number}_mode"

    @property
    def name(self):
        """Return a name to use for this entity."""
        for product in self.coordinator.data:
            if product["serial_number"] == self.product_serial_number:
                for data in product["indicators"]:
                    if data == "MODE":
                        return f"{FRIENDLY_NAMES[self.reference]} {self.product_serial_number} mode"
            return None

    @property
    def current_option(self) -> str:
        return self._mode

    async def async_select_option(self, option: str) -> None:
        """Set mode."""
        await self.coordinator.api.set_mode(self.modem, option)
        await self.coordinator.async_request_refresh()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update attributes when the coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Update select attributes."""
        for product in self.coordinator.data:
            for data_line in product["indicators"][0:]:
                if data_line["type"] == "MODE":
                    self._mode = MODES_TEXT[data_line["value"]]
