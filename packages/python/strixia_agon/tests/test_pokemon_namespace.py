"""Smoke test the game-specific namespace without speculative mechanics."""

from strixia_agon import pokemon


def test_pokemon_namespace() -> None:
    """Pokémon is importable within its owning Agon package."""
    assert pokemon.__name__ == "strixia_agon.pokemon"
