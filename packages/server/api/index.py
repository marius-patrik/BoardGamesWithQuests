"""ASGI entrypoint for the authoritative BoardGamesWithQuests API.

Routes are registered only when they implement supported product contracts.
"""

from fastapi import FastAPI

app = FastAPI(title="BoardGamesWithQuests")
