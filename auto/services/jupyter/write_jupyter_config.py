import sys
import time

from notebook.auth import passwd

from auto.capabilities import list_caps, acquire, release


def go(template_path, output_path):
    caps = list_caps()

    if 'Credentials' not in caps:
        sys.exit(1)

    creds = acquire('Credentials')
    jupyter_password = None

    while True:
        jupyter_password = creds.get_jupyter_password()
        if jupyter_password is not None:
            break
        time.sleep(1)

    release(creds)

    hashed_password = passwd(jupyter_password)

    with open(template_path, 'r') as f:
        f_text = f.read()
        with open(output_path, 'w') as f_out:
            f_out_text = f_text.replace(r'<JUPYTER_PASSWORD>', repr(hashed_password))
            f_out.write(f_out_text)


if __name__ == '__main__':
    template_path = sys.argv[1]
    output_path = sys.argv[2]
    go(template_path, output_path)

