"""Two compact untrained policy/value hypotheses over complete player evidence.

The scalar value is unconstrained and uncalibrated. No learning or persistent memory
is implemented here. Tensor containers are frozen; callers must not mutate tensors.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn

from .representation import (
    KNOWN,
    NUMERIC_FIELDS,
    SCHEMA,
    Candidate,
    Features,
    Observation,
)

WIDTH = 128
PARTS = 4


@dataclass(frozen=True)
class FeatureBatch:
    categories: Tensor
    values: Tensor
    states: Tensor
    mask: Tensor


@dataclass(frozen=True)
class HistoryBatch:
    events: FeatureBatch
    context: FeatureBatch

    @property
    def mask(self) -> Tensor:
        return self.events.mask


@dataclass(frozen=True)
class TensorBatch:
    pokemon: FeatureBatch
    field: FeatureBatch
    history: HistoryBatch
    parts: FeatureBatch
    references: Tensor
    candidate_mask: Tensor


@dataclass(frozen=True)
class PolicyValueOutput:
    logits: Tensor
    value: Tensor
    candidate_mask: Tensor

    def probabilities(self) -> Tensor:
        """Normalize valid menus only; padding and terminal rows stay exactly zero."""
        if self.logits.shape[1] == 0:
            return torch.zeros_like(self.logits)
        active = self.candidate_mask.any(dim=1, keepdim=True)
        safe = torch.where(active, self.logits, torch.zeros_like(self.logits))
        return safe.softmax(dim=1) * self.candidate_mask


def _pack(
    rows: Sequence[Sequence[Features | None]],
    shape: tuple[int, ...],
    device: torch.device,
) -> FeatureBatch:
    categories = max((len(f.categories) for row in rows for f in row if f), default=1)
    cats = torch.zeros((*shape, max(1, categories)), dtype=torch.long, device=device)
    values = torch.zeros((*shape, len(NUMERIC_FIELDS)), device=device)
    states = torch.zeros((*shape, len(NUMERIC_FIELDS)), dtype=torch.long, device=device)
    mask = torch.zeros(shape, dtype=torch.bool, device=device)
    cflat = cats.reshape(len(rows), -1, cats.shape[-1])
    vflat = values.reshape(len(rows), -1, values.shape[-1])
    sflat = states.reshape(len(rows), -1, states.shape[-1])
    mflat = mask.reshape(len(rows), -1)
    for i, row in enumerate(rows):
        for j, feature in enumerate(row):
            if feature is None:
                continue
            if len(feature.values) != len(NUMERIC_FIELDS) or len(feature.states) != len(
                NUMERIC_FIELDS
            ):
                raise ValueError("Features must use the complete numeric schema")
            if any(s not in range(4) for s in feature.states) or any(
                c <= 0 for c in feature.categories
            ):
                raise ValueError("Invalid numeric states or category identifiers")
            cflat[i, j, : len(feature.categories)] = torch.tensor(
                feature.categories, device=device
            )
            vflat[i, j] = torch.tensor(feature.values, device=device)
            sflat[i, j] = torch.tensor(feature.states, device=device)
            mflat[i, j] = True
    return FeatureBatch(cats, values, states, mask)


def batch(
    observations: Sequence[Observation], device: str | torch.device
) -> TensorBatch:
    """Dynamically pad full histories/menus, never discard evidence or actions."""
    if not observations:
        raise ValueError("Cannot batch an empty observation sequence")
    if any(o.schema != SCHEMA for o in observations):
        raise ValueError("Unsupported observation schema")
    if any(o.mechanics_id != observations[0].mechanics_id for o in observations):
        raise ValueError("Cannot mix mechanics vocabularies in a batch")
    if any(len(o.pokemon) != 12 for o in observations):
        raise ValueError("Expected ordered 12-Pokemon observations")
    count = len(observations)
    target = torch.device("cpu")
    fields = max(1, max(len(o.field) for o in observations))
    histories = max(1, max(len(o.history) for o in observations))
    contexts = max(
        1, max((len(e.context) for o in observations for e in o.history), default=0)
    )
    menus = max(len(o.candidates) for o in observations)
    # Allocate one dummy menu for packing, then expose the true zero-length terminal axis.
    packed_menus = max(1, menus)
    parts: list[list[Features | None]] = []
    refs = torch.full(
        (count, packed_menus, PARTS, 2), -1, dtype=torch.long, device=target
    )
    menu_mask = torch.zeros((count, packed_menus), dtype=torch.bool, device=target)
    context_rows: list[list[Features | None]] = []
    for i, obs in enumerate(observations):
        part_row: list[Features | None] = []
        for j, candidate in enumerate(obs.candidates):
            _validate_candidate(candidate)
            part_row.extend(candidate.parts)
            part_row.extend([None] * (PARTS - len(candidate.parts)))
            refs[i, j, : len(candidate.references)] = torch.tensor(
                candidate.references, device=target
            )
            menu_mask[i, j] = True
        parts.append(part_row)
        context_row: list[Features | None] = []
        for event in obs.history:
            context_row.extend(event.context)
            context_row.extend([None] * (contexts - len(event.context)))
        context_rows.append(context_row)
    event_features = _pack(
        [tuple(e.features for e in o.history) for o in observations],
        (count, histories),
        target,
    )
    packed_parts = _pack(parts, (count, packed_menus, PARTS), target)
    packed = TensorBatch(
        _pack([o.pokemon for o in observations], (count, 12), target),
        _pack([o.field for o in observations], (count, fields), target),
        HistoryBatch(
            event_features,
            _pack(context_rows, (count, histories, contexts), target),
        ),
        FeatureBatch(
            packed_parts.categories[:, :menus],
            packed_parts.values[:, :menus],
            packed_parts.states[:, :menus],
            packed_parts.mask[:, :menus],
        ),
        refs[:, :menus],
        menu_mask[:, :menus],
    )

    destination = torch.device(device)

    def move(f: FeatureBatch) -> FeatureBatch:
        return FeatureBatch(
            f.categories.to(destination),
            f.values.to(destination),
            f.states.to(destination),
            f.mask.to(destination),
        )

    return TensorBatch(
        move(packed.pokemon),
        move(packed.field),
        HistoryBatch(move(packed.history.events), move(packed.history.context)),
        move(packed.parts),
        packed.references.to(destination),
        packed.candidate_mask.to(destination),
    )


def _validate_candidate(candidate: Candidate) -> None:
    if not 1 <= len(candidate.parts) <= PARTS or len(candidate.parts) != len(
        candidate.references
    ):
        raise ValueError("Candidate requires 1..4 parts with corresponding references")
    if any(
        index not in range(-1, 12) for pair in candidate.references for index in pair
    ):
        raise ValueError("Candidate reference must be -1 or a registered Pokemon index")


def _pool(encoded: Tensor, mask: Tensor) -> Tensor:
    weights = mask.unsqueeze(-1)
    return (encoded * weights).sum(dim=-2) / weights.sum(dim=-2).clamp_min(1)


class _TokenEncoder(nn.Module):
    def __init__(self, vocab_size: int) -> None:
        super().__init__()
        self.categories = nn.Embedding(vocab_size, 32, padding_idx=0)
        self.category_slots = nn.Sequential(nn.Linear(64, 32), nn.ReLU())
        self.projection = nn.Sequential(
            nn.Linear(32 + 5 * len(NUMERIC_FIELDS), WIDTH), nn.ReLU()
        )

    def forward(self, data: FeatureBatch) -> Tensor:
        embedded = cast(Tensor, self.categories(data.categories))
        # Nonlinear slot binding distinguishes registered/current identities and moves.
        slots = _positions(embedded.shape[-2], 32, embedded).expand_as(embedded)
        bound = cast(Tensor, self.category_slots(torch.cat((embedded, slots), dim=-1)))
        categorical = _pool(bound, data.categories != 0)
        state_masks = (
            nn.functional.one_hot(data.states, num_classes=4)
            .to(data.values.dtype)
            .flatten(-2)
        )
        known_values = data.values * (data.states == KNOWN)
        token = cast(
            Tensor,
            self.projection(
                torch.cat((categorical, known_values, state_masks), dim=-1)
            ),
        )
        return token * data.mask.unsqueeze(-1)


def _positions(length: int, width: int, reference: Tensor) -> Tensor:
    positions = torch.arange(
        length, device=reference.device, dtype=reference.dtype
    ).unsqueeze(1)
    rates = torch.exp(
        torch.arange(0, width, 2, device=reference.device, dtype=reference.dtype)
        * (-math.log(10000.0) / width)
    )
    return torch.stack(
        ((positions * rates).sin(), (positions * rates).cos()), dim=-1
    ).flatten(1)


class PolicyValueModel(nn.Module):
    """MLP or two-block attention encoder with the same ordered candidate scorer."""

    def __init__(self, vocab_size: int, kind: str = "mlp") -> None:
        super().__init__()
        if kind not in ("mlp", "attention"):
            raise ValueError("Model kind must be mlp or attention")
        if vocab_size < 3:
            raise ValueError("Vocabulary must include padding, unknown and absent")
        self.kind = kind
        self.tokens = _TokenEncoder(vocab_size)
        self.events = nn.Sequential(nn.Linear(2 * WIDTH, WIDTH), nn.ReLU())
        if kind == "attention":
            self.roles = nn.Embedding(3, WIDTH)
            self.entities = nn.Embedding(12, WIDTH)
            layer = nn.TransformerEncoderLayer(
                WIDTH, 4, 256, dropout=0.0, batch_first=True
            )
            self.attention = nn.TransformerEncoder(layer, 2, enable_nested_tensor=False)
        state_width = 14 * WIDTH if kind == "mlp" else WIDTH
        self.state = nn.Sequential(
            nn.Linear(state_width, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU()
        )
        self.part = nn.Sequential(nn.Linear(3 * WIDTH, WIDTH), nn.ReLU())
        self.policy = nn.Sequential(
            nn.Linear(256 + PARTS * WIDTH, 256), nn.ReLU(), nn.Linear(256, 1)
        )
        self.value = nn.Linear(256, 1)

    def forward(self, data: TensorBatch) -> PolicyValueOutput:
        pokemon = self.tokens(data.pokemon)
        field = self.tokens(data.field)
        history = cast(
            Tensor,
            self.events(
                torch.cat(
                    (
                        self.tokens(data.history.events),
                        _pool(
                            self.tokens(data.history.context), data.history.context.mask
                        ),
                    ),
                    dim=-1,
                )
            ),
        )
        history = history * data.history.mask.unsqueeze(-1)
        if self.kind == "mlp":
            state_input = torch.cat(
                (
                    pokemon.flatten(1),
                    _pool(field, data.field.mask),
                    _pool(history, data.history.mask),
                ),
                dim=-1,
            )
        else:
            # Explicit entity order and unbounded sinusoidal chronology; no recurrent state.
            pokemon = (
                pokemon
                + self.roles.weight[0]
                + cast(Tensor, self.entities(torch.arange(12, device=pokemon.device)))
            )
            field = field + self.roles.weight[1]
            temporal = _positions(history.shape[1], WIDTH, history)
            history = history + self.roles.weight[2] + temporal
            tokens = torch.cat((pokemon, field, history), dim=1)
            mask = torch.cat(
                (data.pokemon.mask, data.field.mask, data.history.mask), dim=1
            )
            attended = cast(Tensor, self.attention(tokens, src_key_padding_mask=~mask))
            state_input = _pool(attended, mask)
        state = cast(Tensor, self.state(state_input))
        references = data.references
        rows = torch.arange(pokemon.shape[0], device=pokemon.device)[
            :, None, None, None
        ]
        selected = pokemon[rows, references.clamp_min(0)] * (references >= 0).unsqueeze(
            -1
        )
        encoded_parts = cast(
            Tensor,
            self.part(
                torch.cat((self.tokens(data.parts), selected.flatten(-2)), dim=-1)
            ),
        )
        encoded_parts = encoded_parts * data.parts.mask.unsqueeze(-1)
        menu_state = state[:, None, :].expand(-1, data.candidate_mask.shape[1], -1)
        logits = cast(
            Tensor,
            self.policy(torch.cat((menu_state, encoded_parts.flatten(-2)), dim=-1)),
        ).squeeze(-1)
        logits = logits.masked_fill(~data.candidate_mask, -torch.inf)
        value = cast(Tensor, self.value(state)).squeeze(-1)
        return PolicyValueOutput(logits, value, data.candidate_mask)
