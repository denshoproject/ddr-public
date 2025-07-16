import re

# "... [ia_external_id:EXTERNALID]; ..."
EXTERNAL_OBJECT_ID_PATTERN = re.compile(r'ia_external_id:([\w._-]+)')
