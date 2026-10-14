"""Untrained model contracts, using real menus and labeled synthetic evidence."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from strixia_agon.pokemon.mechanics import load_mechanics
from strixia_agon.pokemon.representation import Observation, encode
from strixia_agon.pokemon.simulator import ChampionsBattle, TeamMember

# Models are an optional learning extra; explicitly selected learning checks cannot skip.
torch = pytest.importorskip("torch")
from strixia_agon.pokemon.models import PolicyValueModel, batch  # noqa: E402


@pytest.fixture(scope="module")
def samples() -> tuple[int, Observation, Observation, Observation]:
    root = Path(__file__).resolve().parents[4]
    checkout = root / "tmp/pokemon-foundation/showdown"
    if not (checkout / "dist/sim/index.js").exists():
        pytest.skip("Prepare the pinned engine")
    raw = json.loads((root / "docs/planning/pokemon/foundation/teams.json").read_text())
    teams = [
        [
            TeamMember(
                m["species"],
                m["ability"],
                tuple(m["moves"]),
                m["nature"],
                m["evs"],
                gender="M",
            )
            for m in team
        ]
        for team in raw
    ]
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        preview = encode(battle.state.p1, teams[0], mechanics)
        battle.step("team 1234", "team 1234")
        ordinary = encode(battle.state.p1, teams[0], mechanics)
        waiting = encode(replace(battle.state.p1, must_wait=True), teams[0], mechanics)
    return len(mechanics.vocabulary), preview, ordinary, waiting


@pytest.mark.parametrize("kind", ["mlp", "attention"])
def test_permutation_padding_terminal_and_backward(
    samples: tuple[int, Observation, Observation, Observation], kind: str
) -> None:
    torch.set_num_threads(1)
    torch.manual_seed(17)
    vocab, preview, ordinary, waiting = samples
    model = PolicyValueModel(vocab, kind=kind).eval()
    short = replace(ordinary, history=(), field=(), candidates=ordinary.candidates[:3])
    terminal = replace(short, candidates=())
    wait_output = model(batch([waiting], "cpu"))
    assert wait_output.probabilities().tolist() == [[1.0]]
    single = model(batch([short], "cpu"))
    mixed = model(batch([short, preview, terminal], "cpu"))
    torch.testing.assert_close(
        single.logits[0], mixed.logits[0, :3], atol=2e-6, rtol=2e-5
    )
    torch.testing.assert_close(single.value[0], mixed.value[0], atol=2e-6, rtol=2e-5)
    assert torch.count_nonzero(mixed.probabilities()[0, 3:]) == 0
    assert torch.count_nonzero(mixed.probabilities()[2]) == 0
    empty = model(batch([terminal], "cpu"))
    assert empty.logits.shape == (1, 0)
    assert empty.probabilities().shape == (1, 0)
    assert torch.isfinite(empty.value).all()
    permuted = replace(short, candidates=tuple(reversed(short.candidates)))
    flipped = model(batch([permuted], "cpu"))
    torch.testing.assert_close(single.logits.flip(1), flipped.logits)
    torch.testing.assert_close(single.value, flipped.value)
    # A finite synthetic supervised loss checks autograd, not PPO or learning strength.
    model.train()
    output = model(batch([preview, ordinary], "cpu"))
    loss = (
        output.value.square().mean()
        - output.probabilities()[:, 0].clamp_min(1e-12).log().mean()
    )
    loss.backward()
    assert torch.isfinite(loss)
    gradients = [p.grad for p in model.parameters() if p.grad is not None]
    assert gradients and all(torch.isfinite(g).all() for g in gradients)


@pytest.mark.parametrize("kind", ["mlp", "attention"])
def test_context_and_part_references_are_consumed(
    samples: tuple[int, Observation, Observation, Observation], kind: str
) -> None:
    vocab, _, ordinary, _ = samples
    torch.manual_seed(23)
    model = PolicyValueModel(vocab, kind=kind).eval()
    original = model(batch([ordinary], "cpu"))
    changed_history = tuple(replace(e, context=()) for e in ordinary.history)
    no_context = model(batch([replace(ordinary, history=changed_history)], "cpu"))
    assert not torch.allclose(original.value, no_context.value)
    candidate = ordinary.candidates[0]
    changed = replace(candidate, references=tuple((-1, -1) for _ in candidate.parts))
    no_refs = model(batch([replace(ordinary, candidates=(changed,))], "cpu"))
    assert not torch.allclose(original.logits[0, :1], no_refs.logits[0])
    ordered = replace(
        candidate,
        parts=tuple(reversed(candidate.parts)),
        references=tuple(reversed(candidate.references)),
    )
    reordered = model(batch([replace(ordinary, candidates=(ordered,))], "cpu"))
    assert not torch.allclose(original.logits[0, :1], reordered.logits[0])


def test_full_history_and_input_validation(
    samples: tuple[int, Observation, Observation, Observation],
) -> None:
    _, preview, _, _ = samples
    # Synthetic long history repeats evidence, never a claim of a real long battle.
    long = replace(preview, history=preview.history * 80)
    tensors = batch([preview, long], "cpu")
    assert tensors.history.mask.sum(1).tolist() == [
        len(preview.history),
        len(long.history),
    ]
    with pytest.raises(ValueError, match="empty"):
        batch([], "cpu")
    with pytest.raises(ValueError, match="12"):
        batch([replace(preview, pokemon=preview.pokemon[:6])], "cpu")


@pytest.mark.parametrize("kind", ["mlp", "attention"])
def test_category_slot_binding(
    samples: tuple[int, Observation, Observation, Observation], kind: str
) -> None:
    vocab, preview, _, _ = samples
    pokemon = preview.pokemon[0]
    # Synthetic distinct slot identities expose registered/current category binding.
    categories = (pokemon.categories[0], pokemon.categories[2], *pokemon.categories[2:])
    original = replace(
        preview, pokemon=(replace(pokemon, categories=categories), *preview.pokemon[1:])
    )
    swapped = replace(
        original,
        pokemon=(
            replace(
                pokemon, categories=(categories[1], categories[0], *categories[2:])
            ),
            *preview.pokemon[1:],
        ),
    )
    torch.manual_seed(31)
    model = PolicyValueModel(vocab, kind=kind).eval()
    assert not torch.allclose(
        model(batch([original], "cpu")).logits, model(batch([swapped], "cpu")).logits
    )


def test_mixed_schema_rejected(
    samples: tuple[int, Observation, Observation, Observation],
) -> None:
    _, preview, _, _ = samples
    with pytest.raises(ValueError, match="schema"):
        batch([preview, replace(preview, schema="other")], "cpu")
    with pytest.raises(ValueError, match="mechanics"):
        batch([preview, replace(preview, mechanics_id="other")], "cpu")
