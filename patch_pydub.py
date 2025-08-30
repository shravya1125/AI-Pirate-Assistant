import sys
import types

# Fake audioop module so pydub doesn't break
sys.modules["pyaudioop"] = types.ModuleType("pyaudioop")
