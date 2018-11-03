# The remote repo holding AutoAuto curriculum.
export AA_CURRICULUM_REPO="https://github.com/AutoAutoAI/Curriculum.git"

# The "Privileged" user.
export LIBAUTO_PRIV_USER="hacker"

# The "UnPrivileged" user name.
export LIBAUTO_UP_USER="student"

# The local `libauto` repo.
export LIBAUTO_PATH="/opt/libauto"

# Python needs to know...
export PYTHONPATH="$LIBAUTO_PATH:$PYTHONPATH"

# We run the console_ui and the other libauto services under various Anaconda environments.
# This is so that we can nuke those environments and start over in the future if things change.
# This is also so that if the student wants to install things, they can, and it won't mess
# up the console_ui or other services.
#
# It is slow to run `source activate ___`, so we just hard-code the paths to each python
# executable inside the environment we want. This is fast on startup, and gives the correct
# behavior.
export LIBAUTO_CONSOLE_UI_PYTHON="/opt/berryconda3/bc3/envs/console_ui/bin/python"
export LIBAUTO_SERVICES_PYTHON="/opt/berryconda3/bc3/envs/services/bin/python"

