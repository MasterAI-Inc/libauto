# The remote repo holding AutoAuto curriculum.
export AA_CURRICULUM_REPO="https://github.com/AutoAutoAI/Curriculum.git"

# The "Privileged" user.
export LIBAUTO_PRIV_USER="pi"

# The "UnPrivileged" user name.
export LIBAUTO_UP_USER="student"

# The local `libauto` repo.
export LIBAUTO_PATH="/home/$LIBAUTO_PRIV_USER/github/libauto"

# Python needs to know...
export PYTHONPATH="$LIBAUTO_PATH:$PYTHONPATH"

