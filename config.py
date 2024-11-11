import os
from dotenv import dotenv_values

config = {
    **dotenv_values(".env"),
    **dotenv_values(".env.local"),
    **os.environ,
}
print(config)
