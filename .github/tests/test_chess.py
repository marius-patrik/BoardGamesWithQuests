"""Behavioral Chess rules, staged transitions and historical edge cases."""

import pytest
from model.user import UserManager
from model.board import HerniPlocha
from model.move import Tah, Akce
from model.piece import Kral, Dama, Vez, Strelec, Kun, Pesak
from model.player import Hrac
from model.manager import GameManager
from model.validator import RevizorTahu, IllegalAction


def manager(tmp_path):
    u = UserManager(tmp_path)
    u.vytvor_uzivatele("Alice", "Alice")
    u.vytvor_uzivatele("Bob", "Bob")
    return GameManager(u, "alice", "bob")


def play(g, from_, to, kind=None, promo=None):
    moves = [
        m
        for m in g.mozne_tahy(from_)
        if m.kam == to
        and (kind is None or m.typ_tahu == kind)
        and (promo is None or m.promena == promo)
    ]
    assert len(moves) == 1, (from_, to, moves)
    return g.proved_akci(Akce.move(moves[0]))


def empty(*placements):
    b = HerniPlocha(False)
    for square, piece in placements:
        b.poloz(square, piece)
    return b


def test_initial_position_and_moves(tmp_path):
    g = manager(tmp_path)
    assert len(tuple(g.plocha.pole_figurek())) == 32
    assert len(g.mozne_tahy()) == 20
    assert {m.kam for m in g.mozne_tahy((6, 4))} == {(5, 4), (4, 4)}
    result = play(g, (6, 4), (4, 4))
    assert result.reason is None
    assert g.aktivni_barva == "black" and g.revision == 1
    assert g.plocha.vrat_obsah((6, 4)) is None
    assert g.logger.predchozi_tah.typ_tahu == "pawn_double"
    assert g.logger.events[0]["from"] == [6, 4]


def test_side_effect_free_preview_and_rejected_move(tmp_path):
    g = manager(tmp_path)
    before = g.plocha.stav()
    one = g.mozne_tahy()
    two = g.mozne_tahy()
    assert one == two and g.plocha.stav() == before
    with pytest.raises(IllegalAction):
        g.proved_akci(Akce.move(Tah((6, 4), (3, 4))))
    with pytest.raises(IllegalAction):
        g.proved_akci(Akce.move(Tah((1, 4), (3, 4), "pawn_double")))
    assert g.revision == 0 and g.logger.events == [] and g.plocha.stav() == before


def test_fools_mate_and_quest_attribution(tmp_path):
    g = manager(tmp_path)
    for origin, dest in [((6, 5), (5, 5)), ((1, 4), (3, 4)), ((6, 6), (4, 6))]:
        play(g, origin, dest)
    result = play(g, (0, 3), (4, 7))
    assert result.reason == "checkmate" and result.winner == "black"
    assert set(("check", "checkmate")).issubset(result.matched_rule_ids)
    assert result.xp_awarded == 60
    assert g.users.uzivatele["bob"].xp == 60
    assert g.stav == "terminal" and len(g.mozne_tahy()) == 0
    before = g.plocha.stav()
    with pytest.raises(IllegalAction):
        g.proved_akci(Akce.resign())
    assert g.plocha.stav() == before


def test_en_passant_and_double_quest(tmp_path):
    g = manager(tmp_path)
    for fr, to in [
        ((6, 4), (4, 4)),
        ((1, 0), (2, 0)),
        ((4, 4), (3, 4)),
        ((1, 3), (3, 3)),
    ]:
        play(g, fr, to)
    result = play(g, (3, 4), (2, 3), "en_passant")
    assert set(("capture", "en_passant")).issubset(result.matched_rule_ids)
    assert result.xp_awarded == 30
    assert g.plocha.vrat_obsah((3, 3)) is None
    assert isinstance(g.plocha.vrat_obsah((2, 3)), Pesak)
    assert len(g.plocha.vyhozene_figurky_c) == 1


def test_en_passant_expires(tmp_path):
    g = manager(tmp_path)
    for fr, to in [
        ((6, 4), (4, 4)),
        ((1, 0), (2, 0)),
        ((4, 4), (3, 4)),
        ((1, 3), (3, 3)),
        ((7, 6), (5, 5)),
        ((2, 0), (3, 0)),
    ]:
        play(g, fr, to)
    assert not any(m.typ_tahu == "en_passant" for m in g.mozne_tahy((3, 4)))


def test_en_passant_discovered_attack_is_illegal(tmp_path):
    g = manager(tmp_path)
    g.plocha = empty(
        ((3, 4), Kral("white")),
        ((3, 5), Pesak("white", True)),
        ((3, 6), Pesak("black", True)),
        ((3, 7), Vez("black")),
        ((0, 0), Kral("black")),
    )
    prev = Tah((1, 6), (3, 6), "pawn_double")
    options = g.revizor.mozne_tahy(g.plocha, g.hraci["white"], prev, start=(3, 5))
    assert not any(m.typ_tahu == "en_passant" for m in options)


def test_kingside_and_queenside_castle(tmp_path):
    for rook_col, dest, rook_dest, kind in [
        (7, 6, 5, "castle_kingside"),
        (0, 2, 3, "castle_queenside"),
    ]:
        g = manager(tmp_path / str(rook_col))
        g.plocha = empty(
            ((7, 4), Kral("white")),
            ((7, rook_col), Vez("white")),
            ((0, 4), Kral("black")),
        )
        out = play(g, (7, 4), (7, dest), kind)
        assert isinstance(g.plocha.vrat_obsah((7, dest)), Kral)
        assert isinstance(g.plocha.vrat_obsah((7, rook_dest)), Vez)
        assert g.plocha.vrat_obsah((7, 4)) is None
        assert out.xp_awarded == 15 and len(g.logger.events) == 1


def test_castling_through_check_rejected(tmp_path):
    g = manager(tmp_path)
    g.plocha = empty(
        ((7, 4), Kral("white")),
        ((7, 7), Vez("white")),
        ((0, 0), Kral("black")),
        ((0, 5), Vez("black")),
    )
    assert not any(m.typ_tahu.startswith("castle") for m in g.mozne_tahy((7, 4)))


def test_king_capture_never_allowed(tmp_path):
    g = manager(tmp_path)
    g.plocha = empty(((7, 4), Kral("white")), ((0, 0), Kral("black")), ((1, 0), Dama("white")))
    assert not any(m.kam == (0, 0) for m in g.mozne_tahy((1, 0)))


def test_pinned_piece_must_preserve_king(tmp_path):
    g = manager(tmp_path)
    g.plocha = empty(
        ((7, 4), Kral("white")),
        ((6, 4), Vez("white")),
        ((0, 4), Vez("black")),
        ((0, 0), Kral("black")),
    )
    assert not any(m.kam == (6, 3) for m in g.mozne_tahy((6, 4)))
    assert any(m.kam == (5, 4) for m in g.mozne_tahy((6, 4)))


@pytest.mark.parametrize("code,cls", [("Q", Dama), ("R", Vez), ("B", Strelec), ("N", Kun)])
def test_four_promotion_choices(tmp_path, code, cls):
    g = manager(tmp_path)
    g.plocha = empty(((7, 7), Kral("white")), ((0, 7), Kral("black")), ((1, 0), Pesak("white")))
    options = [m for m in g.mozne_tahy((1, 0)) if m.kam == (0, 0)]
    assert {m.promena for m in options} == {"Q", "R", "B", "N"}
    play(g, (1, 0), (0, 0), "promotion", code)
    assert isinstance(g.plocha.vrat_obsah((0, 0)), cls)
    assert g.plocha.vrat_obsah((1, 0)) is None


def test_stalemate(tmp_path):
    g = manager(tmp_path)
    g.plocha = empty(((2, 2), Kral("white")), ((3, 1), Dama("white")), ((0, 0), Kral("black")))
    outcome = play(g, (3, 1), (2, 1))
    assert outcome.reason == "stalemate" and outcome.winner is None
    assert g.stav == "terminal" and g.logger.result == {
        "reason": "stalemate",
        "winner": None,
    }


def test_resignation_has_no_move_coordinates(tmp_path):
    g = manager(tmp_path)
    before = g.plocha.stav()
    outcome = g.proved_akci(Akce.resign())
    assert outcome.reason == "resignation" and outcome.winner == "black"
    assert g.plocha.stav() == before
    assert g.logger.events[0]["type"] == "resignation"
    assert "from" not in g.logger.events[0]


def test_vector_candidates_for_each_piece(tmp_path):
    v = RevizorTahu()
    for cls, expected in [(Kral, 8), (Dama, 27), (Vez, 14), (Strelec, 13), (Kun, 8)]:
        b = empty(((4, 3), cls("white")), ((0, 0), Kral("black")), ((7, 7), Kral("white")))
        moves = v.mozne_tahy(
            b,
            Hrac("white", manager(tmp_path / cls.__name__).users.uzivatele["alice"]),
            start=(4, 3),
        )
        assert len(moves) >= expected - 1, (cls, len(moves))


def test_quests_are_once_per_actor_per_match_and_reset(tmp_path):
    g = manager(tmp_path)
    # White e4, Black d5, White exd5, Black Qxd5, White Nc3 (attacks queen), Black Qe5+.
    play(g, (6, 4), (4, 4))
    play(g, (1, 3), (3, 3))
    first = play(g, (4, 4), (3, 3))
    assert first.xp_awarded == 10 and "capture" in first.matched_rule_ids
    play(g, (0, 3), (3, 3))
    play(g, (7, 1), (5, 2))
    play(g, (3, 3), (3, 4))
    # White can capture a second piece later; the first Capture reward is already marked complete.
    assert g.quest_manager.dokoncil("alice", "capture")
    assert g.quest_manager.dokoncil("bob", "capture")  # Black's queen captured a pawn.
    assert g.users.uzivatele["alice"].xp == 10
    assert g.users.uzivatele["bob"].xp >= 10
    g2 = g.reset()
    assert not g2.quest_manager.dokoncil("alice", "capture")
    assert g2.users.uzivatele["alice"].xp == 10


def test_pawn_attack_squares_distinct_from_push(tmp_path):
    v = RevizorTahu()
    b = empty(((7, 7), Kral("white")), ((0, 7), Kral("black")), ((3, 3), Pesak("white")))
    attacked = v.ohrozena_pole(b, "white")
    assert (2, 2) in attacked and (2, 4) in attacked
    assert (2, 3) not in attacked


def test_king_unmoved_and_rook_moved_back_cannot_castle(tmp_path):
    g = manager(tmp_path)
    g.plocha = empty(((7, 4), Kral("white")), ((7, 7), Vez("white", True)), ((0, 0), Kral("black")))
    assert not any(m.typ_tahu.startswith("castle") for m in g.mozne_tahy((7, 4)))
