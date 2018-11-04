from auto import db
import sys

store = db.secure_db()

jupyter_password = store.get('DEVICE_JUPYTER_PASSWORD', None)

if jupyter_password is None:
    print("ERROR: DEVICE_JUPYTER_PASSWORD is not set", file=sys.stderr)
    sys.exit(1)

template = sys.argv[1]

with open(template, 'r') as f:
    f_text = f.read()
    print(f_text.replace(r'<JUPYTER_PASSWORD>', jupyter_password))

