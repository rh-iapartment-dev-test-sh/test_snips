#!/usr/bin/env python
# coding=utf-8

from hermes_python.hermes import Hermes
from hermes_python.ontology import IntentMessage, Slot
import ConfigParser
import io
from phue import Bridge
from typing import Dict

CONFIG_FILE = "config.ini"


class SnipsConfigParser(ConfigParser.ConfigParser):
    def to_dict(self):
        return {section: {option_name: option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding="utf-8") as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            conf = conf_parser.to_dict()
            ip = conf["secret"]["light_ip"]
            user = conf["secret"]["light_user"]
            no = conf["secret"]["light_no"]
            return ip, user, int(no)
    except (IOError, ConfigParser.Error) as e:
        raise RuntimeError(e)


def get_intent_header(configuration_file):
    try:
        with io.open(configuration_file, encoding="utf-8") as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            conf = conf_parser.to_dict()
            intent_header = conf["secret"]["intent_header"]
            return intent_header
    except (IOError, ConfigParser.Error) as e:
        raise RuntimeError(e)


def to_slot_map(intent_message):
    # type: (IntentMessage) -> Dict[str, Slot]
    slot_map = dict()

    for slot_value, slot in intent_message.slots.iteritems():
        slot_map[slot_value] = slot

    return slot_map


def command(on=True, bri=254):

    return {"on": on, "bri": bri}


def lights_turnoff(hermes, intent_message):
    ip, user, no = read_configuration_file(CONFIG_FILE)

    bridge = Bridge(ip, user)
    print bridge.set_light(no, command(False, 0))

    hermes.publish_end_session(intent_message.session_id, u"ライトを消しました".encode("utf-8"))


def lights_turnoff_ko(hermes, intent_message):
    ip, user, no = read_configuration_file(CONFIG_FILE)

    bridge = Bridge(ip, user)
    print bridge.set_light(no, command(False, 0))
    hermes.publish_end_session(intent_message.session_id, u"조명을 껐습니다".encode("utf-8"))


def lights_set_ko(hermes, intent_message):
    # type: (Hermes, IntentMessage) -> None
    ip, user, no = read_configuration_file(CONFIG_FILE)
    bridge = Bridge(ip, user)

    print bridge.set_light(no, command())
    hermes.publish_end_session(intent_message.session_id, u"라이트를 붙였습니다".encode("utf-8"))


def lights_set(hermes, intent_message):
    # type: (Hermes, IntentMessage) -> None
    ip, user, no = read_configuration_file(CONFIG_FILE)
    bridge = Bridge(ip, user)
    slot_map = to_slot_map(intent_message)

    house_room = slot_map.get("house_room", None)
    if house_room is not None:
        house_room = house_room[0].slot_value.value
        message = u"%sのライトを" % house_room.decode("utf-8")
    else:
        message = u"ライトを"

    intensity_number = slot_map.get("intensity_number", None)
    if intensity_number is None:
        intensity_percentage = slot_map.get("intensity_percentage", None)
        if intensity_percentage is None:
            print bridge.set_light(no, command(True, 254))
            message += u"最大値でつけました"
        else:
            percentage = intensity_percentage.slot_value.value
            brightness = int(254 * float(0.01 * percentage))
            print bridge.set_light(no, command(True, brightness))
            message += u"%dでつけました" % percentage
    else:
        if u"割" in intent_message.input:
            percentage = intensity_number.slot_value.value
            if percentage > 1:
                print bridge.set_light(no, command(bri=254))
                message += u"最大値でつけました"
            else:
                print bridge.set_light(no, command(bri=254*percentage))
                message += u"%dでつけました" % percentage
        else:
            value = intensity_number.slot_value.value
            if value > 254 or value < 0:
                message = "0から254で指定してください"
            else:
                print bridge.set_light(no, command(bri=value))

    hermes.publish_end_session(intent_message.session_id, message.encode("utf-8"))


def lights_shift_ko(hermes, intent_message):
    # type: (Hermes, IntentMessage) -> None
    ip, user, no = read_configuration_file(CONFIG_FILE)
    bridge = Bridge(ip, user)
    slot_map = to_slot_map(intent_message)
    brightness = bridge.get_light(no, "bri")
    print "brightness", brightness

    up_down = slot_map.get("up_down")[0]
    print dir(up_down.slot_value.value.value)
    if up_down.slot_value.value.value == "up":
        up = True
    else:
        up = False
    if up:
        brightness = brightness + 25
        if brightness > 254:
            brightness = 254
            message += u"最大値でつけました"
        else:
            message += u"明るくしました"
        print bridge.set_light(no, command(bri=brightness))
    else:
        brightness = brightness - 25
        if brightness < 0:
            brightness = 0
            message += u"消しました"
        else:
            message += u"暗くしました"
        print bridge.set_light(no, command(bri=brightness))


def lights_shift(hermes, intent_message):
    # type: (Hermes, IntentMessage) -> None
    ip, user, no = read_configuration_file(CONFIG_FILE)
    bridge = Bridge(ip, user)
    slot_map = to_slot_map(intent_message)
    brightness = bridge.get_light(no, "bri")
    print "brightness", brightness
    house_room = slot_map.get("house_room", None)
    if house_room is not None:
        house_room = house_room[0].raw_value
        message = u"%sのライトを" % house_room.decode("utf-8")
    else:
        message = u"ライトを"

    up_down = slot_map.get("up_down")[0]
    print dir(up_down.slot_value.value.value)  
    if up_down.slot_value.value.value == "up":
        up = True
    else:
        up = False

    intensity_number = slot_map.get("intensity_number", None)
    if intensity_number is None:
        intensity_percentage = slot_map.get("intensity_percentage", None)

        if intensity_percentage is None:
            if up:
                brightness = brightness + 25
                if brightness > 254:
                    brightness = 254
                    message += u"最大値でつけました"
                else:
                    message += u"明るくしました"
                print bridge.set_light(no, command(bri=brightness))
            else:
                brightness = brightness - 25
                if brightness < 0:
                    brightness = 0
                    message += u"消しました"
                else:
                    message += u"暗くしました"
                print bridge.set_light(no, command(bri=brightness))

        else:
            percentage = intensity_percentage[0].slot_value.value
            print "percentage", percentage
            brightness_delta = int(254 * float(0.01 * percentage))
            print "delta", brightness_delta
            if up:
                brightness += brightness_delta
                print "brightness up", brightness
                if brightness > 254:
                    brightness = 254
                    message += u"最大値でつけました"
                else:
                    message += u"%d%%明るくしました" % percentage
            else:
                brightness -= brightness_delta
                print "brightness down", brightness
                if brightness < 0:
                    brightness = 0
                    message += u"暗くしました"
                else:
                    message += u"%d%%暗くしました" % percentage
            print brightness
            print bridge.set_light(no, command(bri=int(brightness)))
            message += u"%dでつけました" % percentage
    else:
        intensity_number = intensity_number[0]
        if u"割" in intent_message.input:
            percentage = intensity_number.slot_value.value * 0.1
            if percentage > 1:
                print bridge.set_light(no, command(bri=254))
                message += u"最大値でつけました"
            else:
                print bridge.set_light(no, command(bri=254*percentage))
                message += u"%dでつけました" % percentage
        else:
            value = intensity_number.slot_value.value
            if value > 254 or value < 0:
                message = "0から254で指定してください"
            else:
                if up:
                    brightness += value
                    if brightness > 254:
                        brightness = 254
                    message += u"明るくしました"
                else:
                    brightness -= value
                    if brightness < 0:
                        brightness = 0
                    message += u"暗くしました"

                print bridge.set_light(no, command(bri=brightness))

    hermes.publish_end_session(intent_message.session_id, message.encode("utf-8"))


with Hermes('localhost:1883') as h:
    intent_header = get_intent_header(CONFIG_FILE)
    h.subscribe_intent(intent_header+":lightsTurnOff", lights_turnoff).\
        subscribe_intent(intent_header+":lightsSet", lights_set).\
        subscribe_intent(intent_header+":lightsShift", lights_shift). \
        subscribe_intent(intent_header+":lightsTurnOff_ko", lights_turnoff_ko).\
        subscribe_intent(intent_header+":lightsSet_ko", lights_set_ko). \
        subscribe_intent(intent_header+":lightsShift_ko", lights_shift_ko).\
        start()
