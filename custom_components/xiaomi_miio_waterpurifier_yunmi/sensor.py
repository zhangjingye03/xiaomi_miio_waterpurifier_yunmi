"""
Support for Xiaomi Water Purifier C1.
"""

import asyncio
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.const import (
    CONF_HOST, 
    CONF_NAME,
    CONF_TOKEN, 
    TEMP_CELSIUS
)

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from miio import Device, DeviceException
from miio.waterpurifier_yunmi import WaterPurifierYunmi

_LOGGER = logging.getLogger(__name__)

ATTR_ERROR_REASON = "operation_status"
ATTR_F1_REMAINTIME = "filter1_life_remaining"
ATTR_F1_USEDTIME = "filter1_life_used"
ATTR_F1_REMAINFLOW = "filter1_flow_remaining"
ATTR_F1_USEDFLOW = "filter1_flow_used"
ATTR_F2_REMAINTIME = "filter2_life_remaining"
ATTR_F2_USEDTIME = "filter2_life_used"
ATTR_F2_REMAINFLOW = "filter2_flow_remaining"
ATTR_F2_USEDFLOW = "filter2_flow_used"
ATTR_F3_REMAINTIME = "filter3_life_remaining"
ATTR_F3_USEDTIME = "filter3_life_used"
ATTR_F3_REMAINFLOW = "filter3_flow_remaining"
ATTR_F3_USEDFLOW = "filter3_flow_used"
ATTR_TDS_IN = "tds_in"
ATTR_TDS_OUT = "tds_out"
ATTR_RINSE = "rinse"
ATTR_TEMPERATURE = "temperature"
# ATTR_TDS_WARN_THD = "tds_warn_thd"

ATTRIBUTE_IS_TIMEDELTA = [
    ATTR_F1_REMAINTIME,
    ATTR_F2_REMAINTIME,
    ATTR_F3_REMAINTIME,
    ATTR_F1_USEDTIME,
    ATTR_F2_USEDTIME,
    ATTR_F3_USEDTIME,
]

AVAILABLE_ATTRIBUTES = {
    ATTR_ERROR_REASON:
        {'name': "Error reason", 'unit': None, 'icon': 'mdi:alert-circle-outline'},
    ATTR_F1_REMAINTIME:
        {'name': "Filter#1 (PPC) remaining time", 'unit': 'h', 'icon': 'mdi:timer-sand'},
    ATTR_F1_USEDTIME:
        {'name': "Filter#1 (PPC) used time", 'unit': 'h', 'icon': 'mdi:timer-sand-complete'},
    ATTR_F1_REMAINFLOW:
        {'name': "Filter#1 (PPC) remaining flow", 'unit': 'L', 'icon': 'mdi:timer-sand'},
    ATTR_F1_USEDFLOW:
        {'name': "Filter#1 (PPC) used flow", 'unit': 'L', 'icon': 'mdi:timer-sand-complete'},
    ATTR_F2_REMAINTIME:
        {'name': "Filter#2 (RO) remaining time", 'unit': 'h', 'icon': 'mdi:timer-sand'},
    ATTR_F2_USEDTIME:
        {'name': "Filter#2 (RO) used time", 'unit': 'h', 'icon': 'mdi:timer-sand-complete'},
    ATTR_F2_REMAINFLOW:
        {'name': "Filter#2 (RO) remaining flow", 'unit': 'L', 'icon': 'mdi:timer-sand'},
    ATTR_F2_USEDFLOW:
        {'name': "Filter#2 (RO) used flow", 'unit': 'L', 'icon': 'mdi:timer-sand-complete'},
    ATTR_F3_REMAINTIME:
        {'name': "Filter#3 (CB) remaining time", 'unit': 'h', 'icon': 'mdi:timer-sand'},
    ATTR_F3_USEDTIME:
        {'name': "Filter#3 (CB) used time", 'unit': 'h', 'icon': 'mdi:timer-sand-complete'},
    ATTR_F3_REMAINFLOW:
        {'name': "Filter#3 (CB) remaining flow", 'unit': 'L', 'icon': 'mdi:timer-sand'},
    ATTR_F3_USEDFLOW:
        {'name': "Filter#3 (CB) used flow", 'unit': 'L', 'icon': 'mdi:timer-sand-complete'},
    ATTR_TDS_IN:
        {'name': 'In water TDS', 'unit': 'ppm', 'icon': 'mdi:water-percent'},
    ATTR_TDS_OUT:
        {'name': "Out water TDS", 'unit': 'ppm', 'icon': 'mdi:water-percent'},
    ATTR_RINSE:
        {'name': "Rinsing", 'unit': None, 'icon': 'mdi:shower-head'},
    ATTR_TEMPERATURE:
        {'name': "Water temperature", 'unit': TEMP_CELSIUS, 'icon': 'mdi:thermometer'},
    # ATTR_TDS_WARN_THD:
    #     {'name': 'TDS warning threshold', 'unit': "ppm", 'icon': 'mdi:water-percent-alert'},
}

CONF_MODEL = "model"
CONF_RETRIES = "retries"

DATA_KEY = "sensor.xiaomi_miio_waterpurifier_yunmi"
DEFAULT_NAME = "Xiaomi Water Purifier C1"
DEFAULT_RETRIES = 60

MODEL_WATERPURI_LX9 = "yunmi.waterpuri.lx9"
MODEL_WATERPURI_LX11 = "yunmi.waterpuri.lx11"

MODELS_SUPPORTED = [
    MODEL_WATERPURI_LX9,
    MODEL_WATERPURI_LX11,
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
    }
)

SUCCESS = ["ok"]


# pylint: disable=unused-argument
@asyncio.coroutine
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Water Purifier Yunmi Model from config."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    model = config.get(CONF_MODEL)
    retries = config.get(CONF_RETRIES)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = miio_device.info()
            model = device_info.model
            unique_id = f"{model}-{device_info.mac_address}"
            _LOGGER.info(
                "%s %s %s detected",
                model,
                device_info.firmware_version,
                device_info.hardware_version,
            )
        except:
            raise PlatformNotReady

    if model in MODELS_SUPPORTED:
        waterpuri = WaterPurifierYunmi(host, token)

    else:
        _LOGGER.error(
            "Unsupported device %s found!",
            model,
        )
        return

    hass.data[DATA_KEY][host] = {
        'device': waterpuri,
        'state': None,
        'retry': 0,
        'retries': retries,
    }


    async def async_update_data():
        """Fetch state from the device."""
        data = hass.data[DATA_KEY][host]
        data['retry'] = 0
        _LOGGER.debug("Updating, retry: " + str(data['retry']))
        while data['retry'] < data['retries']:
            try:
                state = await hass.async_add_executor_job(waterpuri.status)
                _LOGGER.debug("Got new state: %s", state)
                data['retry'] = 0
                return state

            except DeviceException as ex:
                data['retry'] = data['retry'] + 1
                _LOGGER.info(
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    data['retry'],
                )
                if data['retry'] >= data['retries']:
                    raise UpdateFailed(f"Error communicating with water purifier: {ex}")
    
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="xiaomi_miio_waterpurifier_yunmi_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=300),
    )

    await coordinator.async_refresh()

    async_add_entities(
        XiaomiWaterPurifierYunmiSensor(coordinator, i, unique_id, name) for i in AVAILABLE_ATTRIBUTES
    )

class WaterPurifierYunmiException(DeviceException):
    pass


class XiaomiWaterPurifierYunmiSensor(CoordinatorEntity):
    """Representation of Xiaomi Water Purifier Yunmi sensors."""

    ### Device initialization and registration

    def __init__(self, coordinator, state_name, unique_id, name):
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._state_name = state_name
        self._unique_id = f"{unique_id}-{state_name}"
        self._name = name + " " + AVAILABLE_ATTRIBUTES[state_name]['name']
        self._unit_of_measurement = AVAILABLE_ATTRIBUTES[state_name]['unit']
        self._icon = AVAILABLE_ATTRIBUTES[state_name]['icon']

    ### Implement abstract `Entity` class

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def icon(self) -> str:
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        ret = getattr(self.coordinator.data, self._state_name)

        if self._state_name in ATTRIBUTE_IS_TIMEDELTA:
            return ret.total_seconds() // 3600
        
        elif self._state_name == ATTR_ERROR_REASON:
            if len(getattr(ret, "errors")) == 0:
                return "None"
            return ", ".join(i["name"] for i in getattr(ret, "errors"))

        return ret
