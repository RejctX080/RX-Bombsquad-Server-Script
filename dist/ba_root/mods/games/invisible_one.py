# Released under the MIT License. See LICENSE for details.
#
# By itsre3
# =>3<=
# Don't mind my spelling. i realized that they were not correct after making last change and saving
# Besides that, enjoy.......!!
"""Provides the chosen-one mini-game."""

# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor.flag import Flag
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.scoreboard import Scoreboard
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Optional, Sequence, Union


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.chosen_light: Optional[ba.NodeActor] = None


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self, time_remaining: int) -> None:
        self.time_remaining = time_remaining


# ba_meta export game
class InvicibleOneGame(ba.TeamGameActivity[Player, Team]):
    """
    Game involving trying to remain the one 'invisible one'
    for a set length of time while everyone else tries to
    kill you and become the invisible one themselves.
    """

    name = 'Invisible One'
    description = ('Be the invisible one for a length of time to win.\n'
                   'Kill the invisible one to become it.')
    available_settings = [
        ba.IntSetting(
            'Invicible One Time',
            min_value=10,
            default=30,
            increment=10,
        ),
        ba.BoolSetting('Invicible one is lazy', default=True),
        ba.BoolSetting('Night mode', default=False),
        ba.IntChoiceSetting(
            'Time Limit',
            choices=[
                ('None', 0),
                ('1 Minute', 60),
                ('2 Minutes', 120),
                ('5 Minutes', 300),
                ('10 Minutes', 600),
                ('20 Minutes', 1200),
            ],
            default=0,
        ),
        ba.FloatChoiceSetting(
            'Respawn Times',
            choices=[
                ('Shorter', 0.25),
                ('Short', 0.5),
                ('Normal', 1.0),
                ('Long', 2.0),
                ('Longer', 4.0),
            ],
            default=1.0,
        ),
        ba.BoolSetting('Epic Mode', default=False),
    ]
    scoreconfig = ba.ScoreConfig(label='Time Held')

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('keep_away')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._invicible_one_player: Optional[Player] = None
        self._swipsound = ba.getsound('swip')
        self._countdownsounds: Dict[int, ba.Sound] = {
            10: ba.getsound('announceTen'),
            9: ba.getsound('announceNine'),
            8: ba.getsound('announceEight'),
            7: ba.getsound('announceSeven'),
            6: ba.getsound('announceSix'),
            5: ba.getsound('announceFive'),
            4: ba.getsound('announceFour'),
            3: ba.getsound('announceThree'),
            2: ba.getsound('announceTwo'),
            1: ba.getsound('announceOne')
        }
        self._flag_spawn_pos: Optional[Sequence[float]] = None
        self._reset_region_material: Optional[ba.Material] = None
        self._flag: Optional[Flag] = None
        self._reset_region: Optional[ba.Node] = None
        self._epic_mode = bool(settings['Epic Mode'])
        self._invicible_one_time = int(settings['Invicible One Time'])
        self._time_limit = float(settings['Time Limit'])
        self._invicible_one_is_lazy = bool(settings['Invicible one is lazy'])
        self._night_mode = bool(settings['Night mode'])

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.CHOSEN_ONE)

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Show your invisibility powers.'

    def create_team(self, sessionteam: ba.SessionTeam) -> Team:
        return Team(time_remaining=self._invicible_one_time)

    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        if self._get_invicible_one_player() is player:
            self._set_invicible_one_player(None)

    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        Flag.project_stand(self._flag_spawn_pos)
        self._set_invicible_one_player(None)
        if self._night_mode:
            gnode = ba.getactivity().globalsnode
            gnode.tint = (0.4, 0.4, 0.4)

        pos = self._flag_spawn_pos
        ba.timer(1.0, call=self._tick, repeat=True)

        mat = self._reset_region_material = ba.Material()
        mat.add_actions(
            conditions=(
                'they_have_material',
                shared.player_material,
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 ba.WeakCall(self._handle_reset_collide)),
            ),
        )

        self._reset_region = ba.newnode('region',
                                        attrs={
                                            'position': (pos[0], pos[1] + 0.75,
                                                         pos[2]),
                                            'scale': (0.5, 0.5, 0.5),
                                            'type': 'sphere',
                                            'materials': [mat]
                                        })

    def _get_invicible_one_player(self) -> Optional[Player]:
        # Should never return invalid references; return None in that case.
        if self._invicible_one_player:
            return self._invicible_one_player
        return None

    def _handle_reset_collide(self) -> None:
        # If we have a chosen one, ignore these.
        if self._get_invicible_one_player() is not None:
            return

        # Attempt to get a Player controlling a Spaz that we hit.
        try:
            player = ba.getcollision().opposingnode.getdelegate(
                PlayerSpaz, True).getplayer(Player, True)
        except ba.NotFoundError:
            return

        if player.is_alive():
            self._set_invicible_one_player(player)

    def _flash_flag_spawn(self) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': self._flag_spawn_pos,
                               'color': (1, 1, 1),
                               'radius': 0.3,
                               'height_attenuated': False
                           })
        ba.animate(light, 'intensity', {0: 0, 0.25: 0.5, 0.5: 0}, loop=True)
        ba.timer(1.0, light.delete)

    def _tick(self) -> None:

        # Give the chosen one points.
        player = self._get_invicible_one_player()
        if player is not None:

            # This shouldn't happen, but just in case.
            if not player.is_alive():
                ba.print_error('got dead player as chosen one in _tick')
                self._set_invicible_one_player(None)
            else:
                scoring_team = player.team
                assert self.stats
                self.stats.player_scored(player,
                                         3,
                                         screenmessage=False,
                                         display=False)

                scoring_team.time_remaining = max(
                    0, scoring_team.time_remaining - 1)

                self._update_scoreboard()

                # announce numbers we have sounds for
                if scoring_team.time_remaining in self._countdownsounds:
                    ba.playsound(
                        self._countdownsounds[scoring_team.time_remaining])

                # Winner!
                if scoring_team.time_remaining <= 0:
                    self.end_game()

        else:
            # (player is None)
            # This shouldn't happen, but just in case.
            # (Chosen-one player ceasing to exist should
            # trigger on_player_leave which resets chosen-one)
            if self._invicible_one_player is not None:
                ba.print_error('got nonexistent player as chosen one in _tick')
                self._set_invicible_one_player(None)

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team,
                                   self._invicible_one_time - team.time_remaining)
        self.end(results=results, announce_delay=0)

    def _set_invicible_one_player(self, player: Optional[Player]) -> None:
        existing = self._get_invicible_one_player()
        if existing:
            existing.chosen_light = None
        ba.playsound(self._swipsound)
        if not player:
            assert self._flag_spawn_pos is not None
            self._flag = Flag(color=(1, 0.9, 0.2),
                              position=self._flag_spawn_pos,
                              touchable=False)
            self._invicible_one_player = None

            # Create a light to highlight the flag;
            # this will go away when the flag dies.
            ba.newnode('light',
                       owner=self._flag.node,
                       attrs={
                           'position': self._flag_spawn_pos,
                           'intensity': 0.6,
                           'height_attenuated': False,
                           'volume_intensity_scale': 0.1,
                           'radius': 0.1,
                           'color': (1.2, 1.2, 0.4)
                       })

            # Also an extra momentary flash.
            self._flash_flag_spawn()
        else:
            if player.actor:
                self._flag = None
                self._invicible_one_player = player

                if self._invicible_one_is_lazy:
                    player.actor.connect_controls_to_player(
                        enable_punch=False, enable_pickup=False, enable_bomb=False)
                if player.actor.node.torso_model != None:
                    player.actor.node.color_mask_texture = None
                    player.actor.node.color_texture = None
                    player.actor.node.head_model = None
                    player.actor.node.torso_model = None
                    player.actor.node.upper_arm_model = None
                    player.actor.node.forearm_model = None
                    player.actor.node.pelvis_model = None
                    player.actor.node.toes_model = None
                    player.actor.node.upper_leg_model = None
                    player.actor.node.lower_leg_model = None
                    player.actor.node.hand_model = None
                    player.actor.node.style = 'cyborg'
                    invi_sound = []
                    player.actor.node.jump_sounds = invi_sound
                    player.actor.attack_sounds = invi_sound
                    player.actor.impact_sounds = invi_sound
                    player.actor.pickup_sounds = invi_sound
                    player.actor.death_sounds = invi_sound
                    player.actor.fall_sounds = invi_sound

                player.actor.node.name = ''

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if player is self._get_invicible_one_player():
                killerplayer = msg.getkillerplayer(Player)
                self._set_invicible_one_player(None if (
                    killerplayer is None or killerplayer is player
                    or not killerplayer.is_alive()) else killerplayer)
            self.respawn_player(player)
        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team,
                                            team.time_remaining,
                                            self._invicible_one_time,
                                            countdown=True)
