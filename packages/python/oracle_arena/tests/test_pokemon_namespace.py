"""Smoke test the game-specific namespace without speculative mechanics."""

from oracle_arena import pokemon


def test_pokemon_namespace() -> None:
    """Pokémon is importable within its owning Arena package."""
    assert pokemon.__name__ == "oracle_arena.pokemon"
