import sys
import re
import xml.etree.ElementTree as ET

from ncclient import manager

pot_profile_name = sys.argv[1]
config = ET.Element('config')
config.set('xmlns', 'urn:ietf:params:xml:ns:netconf:base:1.0')
config.set('xmlns:nc', 'urn:ietf:params:xml:ns:netconf:base:1.0')
pot_profiles = ET.SubElement(config, 'pot-profiles')
pot_profiles.set('xmlns', 'urn:ietf:params:xml:ns:yang:ietf-pot-profile')
pot_profile_set = ET.SubElement(pot_profiles, 'pot-profile-set')
pot_profile_set.set('nc:operation', 'delete')
ET.SubElement(pot_profile_set, 'pot-profile-name').text = pot_profile_name
xml_string = ET.tostring(config, encoding='utf8', method='xml').decode()
result = re.sub(r'<\?xml.*?\?>', '', xml_string).strip().encode().decode('utf8')

with manager.connect(host="127.0.0.1",
                     port=830,
                     username="netconf",
                     password="netconf",
                     timeout=90,
                     hostkey_verify=False) as m:
    response = m.edit_config(config=result, target='running')