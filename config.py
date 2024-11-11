import os
from dotenv import dotenv_values

config = {
    **os.environ,
    **dotenv_values(".env"),
    **dotenv_values(".env.local"),
}
