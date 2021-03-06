"""
homeassistant.components
~~~~~~~~~~~~~~~~~~~~~~~~

This package contains components that can be plugged into Home Assistant.

Component design guidelines:

Each component defines a constant DOMAIN that is equal to its filename.

Each component that tracks states should create state entity names in the
format "<DOMAIN>.<OBJECT_ID>".

Each component should publish services only under its own domain.

"""
import itertools as it
import logging

import homeassistant as ha
import homeassistant.util as util
from homeassistant.helpers import extract_entity_ids
from homeassistant.loader import get_component
from homeassistant.const import (
    ATTR_ENTITY_ID, SERVICE_TURN_ON, SERVICE_TURN_OFF)

_LOGGER = logging.getLogger(__name__)


def is_on(hass, entity_id=None):
    """ Loads up the module to call the is_on method.
    If there is no entity id given we will check all. """
    if entity_id:
        group = get_component('group')

        entity_ids = group.expand_entity_ids(hass, [entity_id])
    else:
        entity_ids = hass.states.entity_ids()

    for entity_id in entity_ids:
        domain = util.split_entity_id(entity_id)[0]

        module = get_component(domain)

        try:
            if module.is_on(hass, entity_id):
                return True

        except AttributeError:
            # module is None or method is_on does not exist
            _LOGGER.exception("Failed to call %s.is_on for %s",
                              module, entity_id)

    return False


def turn_on(hass, entity_id=None, **service_data):
    """ Turns specified entity on if possible. """
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(ha.DOMAIN, SERVICE_TURN_ON, service_data)


def turn_off(hass, entity_id=None, **service_data):
    """ Turns specified entity off. """
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(ha.DOMAIN, SERVICE_TURN_OFF, service_data)


def setup(hass, config):
    """ Setup general services related to homeassistant. """

    def handle_turn_service(service):
        """ Method to handle calls to homeassistant.turn_on/off. """
        entity_ids = extract_entity_ids(hass, service)

        # Generic turn on/off method requires entity id
        if not entity_ids:
            _LOGGER.error(
                "homeassistant/%s cannot be called without entity_id",
                service.service)
            return

        # Group entity_ids by domain. groupby requires sorted data.
        by_domain = it.groupby(sorted(entity_ids),
                               lambda item: util.split_entity_id(item)[0])

        for domain, ent_ids in by_domain:
            # Create a new dict for this call
            data = dict(service.data)

            # ent_ids is a generator, convert it to a list.
            data[ATTR_ENTITY_ID] = list(ent_ids)

            hass.services.call(domain, service.service, data, True)

    hass.services.register(ha.DOMAIN, SERVICE_TURN_OFF, handle_turn_service)
    hass.services.register(ha.DOMAIN, SERVICE_TURN_ON, handle_turn_service)

    return True
