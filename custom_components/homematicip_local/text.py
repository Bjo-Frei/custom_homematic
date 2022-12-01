"""text for Homematic(IP) Local."""
from __future__ import annotations

import logging
from typing import Any

from hahomematic.const import HmPlatform
from hahomematic.generic_platforms.text import HmSysvarText, HmText

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONTROL_UNITS, DOMAIN
from .control_unit import ControlUnit, async_signal_new_hm_entity
from .generic_entity import (
    HaHomematicGenericRestoreEntity,
    HaHomematicGenericSysvarEntity,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Homematic(IP) Local text platform."""
    control_unit: ControlUnit = hass.data[DOMAIN][CONTROL_UNITS][config_entry.entry_id]

    @callback
    def async_add_text(args: Any) -> None:
        """Add text from Homematic(IP) Local."""
        entities: list[HaHomematicGenericRestoreEntity] = []

        for hm_entity in args:
            entities.append(HaHomematicText(control_unit, hm_entity))

        if entities:
            async_add_entities(entities)

    @callback
    def async_add_hub_text(args: Any) -> None:
        """Add sysvar text from Homematic(IP) Local."""

        entities = []

        for hm_entity in args:
            entities.append(HaHomematicSysvarText(control_unit, hm_entity))

        if entities:
            async_add_entities(entities)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            async_signal_new_hm_entity(config_entry.entry_id, HmPlatform.TEXT),
            async_add_text,
        )
    )
    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            async_signal_new_hm_entity(config_entry.entry_id, HmPlatform.HUB_TEXT),
            async_add_hub_text,
        )
    )

    async_add_text(
        control_unit.async_get_new_hm_entities_by_platform(platform=HmPlatform.TEXT)
    )

    async_add_hub_text(
        control_unit.async_get_new_hm_entities_by_platform(platform=HmPlatform.HUB_TEXT)
    )


class HaHomematicText(HaHomematicGenericRestoreEntity[HmText], TextEntity):
    """Representation of the HomematicIP text entity."""

    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 255

    @property
    def native_value(self) -> str | None:
        """Return the value reported by the text."""
        if self._hm_entity.is_valid:
            return self._hm_entity.value
        if self.is_restored:
            if (restored_state := self._restored_state.state) not in (  # type: ignore[union-attr]
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ):
                return restored_state
        return None

    async def async_set_value(self, value: str) -> None:
        """Send the text."""
        await self._hm_entity.send_value(value=value)


class HaHomematicSysvarText(HaHomematicGenericSysvarEntity[HmSysvarText], TextEntity):
    """Representation of the HomematicIP hub text entity."""

    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 255

    @property
    def native_value(self) -> str | None:
        """Return the value reported by the text."""
        return self._hm_hub_entity.value

    async def async_set_value(self, value: str) -> None:
        """Send the text."""
        await self._hm_hub_entity.send_variable(value=value)
