from typing import Optional, List, Dict, Any
from ...store.game_store import GameStore
from ...models.game_models import (
    GameState,
    Player,
    PlayerAction,
    ActionType,
    GamePhase,
    HandRank,
    PlayerStatus,
)
from ...core.agents.agent_manager import agent_manager
from datetime import datetime


class GameService:
    """Service layer for game business logic"""

    def __init__(self, store: GameStore):
        self.store = store

    async def make_player_action(
        self,
        game_id: str,
        player_id: str,
        action_type: str,
        amount: Optional[int] = None,
    ) -> bool:
        """Make a player action with business logic validation"""

        # Get the game state
        game = self.store.get_game(game_id)
        if not game:
            return False

        # Find the player
        player = next((p for p in game.players if p.id == player_id), None)
        if not player:
            return False

        # Validate it's the player's turn
        if (
            game.active_player_index is None
            or game.players[game.active_player_index].id != player_id
        ):
            return False

        # Validate the action
        if not self._validate_action(player, game, action_type, amount):
            return False

        # Create the action
        action = PlayerAction(
            player_id=player_id,
            action_type=ActionType(action_type),
            amount=amount,
            timestamp=datetime.now(),
        )

        # Apply the action to the game state
        success = await self._apply_action(game, player, action)
        if not success:
            return False

        # Record the action
        game.action_history.append(action)
        game.last_action = action

        # Update game state
        await self._update_game_state(game)

        # Update the store
        self.store.active_games[game_id] = game

        return True

    def _validate_action(
        self, player: Player, game: GameState, action_type: str, amount: Optional[int]
    ) -> bool:
        """Validate if an action is legal"""

        # Check if player is still in the game
        if player.status == PlayerStatus.FOLDED:
            return False

        # Check if player has enough chips for the action
        if action_type in ["call", "raise", "all_in"]:
            call_amount = game.current_bet - player.current_bet

            if action_type == "call":
                if player.chips < call_amount:
                    return False
            elif action_type == "raise":
                if amount is None or amount <= game.current_bet:
                    return False
                if player.chips < amount:
                    return False
                if amount < game.min_raise:
                    return False
            elif action_type == "all_in":
                if player.chips <= 0:
                    return False

        # Check if action is available in current phase
        if action_type == "check" and game.current_bet > player.current_bet:
            return False

        return True

    async def _apply_action(
        self, game: GameState, player: Player, action: PlayerAction
    ) -> bool:
        """Apply an action to the game state"""

        if action.action_type == ActionType.FOLD:
            player.status = PlayerStatus.FOLDED
            return True

        elif action.action_type == ActionType.CHECK:
            # Check is always valid if no bet to call
            return True

        elif action.action_type == ActionType.CALL:
            call_amount = game.current_bet - player.current_bet
            if player.chips < call_amount:
                return False

            player.chips -= call_amount
            player.current_bet = game.current_bet
            game.pot += call_amount
            return True

        elif action.action_type == ActionType.RAISE:
            if action.amount is None or action.amount <= game.current_bet:
                return False

            raise_amount = action.amount - player.current_bet
            if player.chips < raise_amount:
                return False

            player.chips -= raise_amount
            player.current_bet = action.amount
            game.pot += raise_amount
            game.current_bet = action.amount
            game.min_raise = action.amount - game.current_bet

            return True

        elif action.action_type == ActionType.ALL_IN:
            all_in_amount = player.chips
            player.current_bet += all_in_amount
            game.pot += all_in_amount
            player.chips = 0
            player.status = PlayerStatus.ALL_IN

            # Update current bet if this is the highest
            if player.current_bet > game.current_bet:
                game.current_bet = player.current_bet
                game.min_raise = player.current_bet - game.current_bet

            return True

        return False

    async def _update_game_state(self, game: GameState) -> None:
        """Update game state after an action"""

        # Check if round is complete
        active_players = [p for p in game.players if p.status == PlayerStatus.ACTIVE]

        # Check if all active players have matched the current bet
        all_matched = all(p.current_bet == game.current_bet for p in active_players)

        if all_matched and len(active_players) > 1:
            # Round is complete, move to next phase
            await self._advance_game_phase(game)
        else:
            # Move to next player
            await self._move_to_next_player(game)

    async def _move_to_next_player(self, game: GameState) -> None:
        """Move to the next active player"""
        if game.active_player_index is None:
            return

        # Find next active player
        next_index = (game.active_player_index + 1) % len(game.players)
        while next_index != game.active_player_index:
            if game.players[next_index].status == PlayerStatus.ACTIVE:
                game.active_player_index = next_index
                return
            next_index = (next_index + 1) % len(game.players)

    async def _advance_game_phase(self, game: GameState) -> None:
        """Advance the game to the next phase"""

        # Reset player betting state
        for player in game.players:
            player.current_bet = 0

        # Reset betting state
        game.current_bet = 0
        game.min_raise = game.big_blind

        # Advance phase
        if game.phase == GamePhase.PRE_FLOP:
            game.phase = GamePhase.FLOP
            # Deal flop (this would need deck implementation)
            # game.community_cards = game.deck.deal_community_cards(3)
        elif game.phase == GamePhase.FLOP:
            game.phase = GamePhase.TURN
            # Deal turn
            # game.community_cards.extend(game.deck.deal_community_cards(1))
        elif game.phase == GamePhase.TURN:
            game.phase = GamePhase.RIVER
            # Deal river
            # game.community_cards.extend(game.deck.deal_community_cards(1))
        elif game.phase == GamePhase.RIVER:
            game.phase = GamePhase.SHOWDOWN
            await self._determine_winner(game)
            return

        # Set first active player after dealer
        active_players = [
            i for i, p in enumerate(game.players) if p.status == PlayerStatus.ACTIVE
        ]
        if active_players:
            game.active_player_index = active_players[0]

    async def _determine_winner(self, game: GameState) -> None:
        """Determine the winner of the hand"""

        # Get active players
        active_players = [
            p
            for p in game.players
            if p.status in [PlayerStatus.ACTIVE, PlayerStatus.ALL_IN]
        ]

        if len(active_players) == 1:
            # Only one player left, they win
            winner = active_players[0]
            winner.chips += game.pot
            game.pot = 0
        else:
            # Evaluate hands (this would need hand evaluation implementation)
            # For now, just split pot among active players
            split_amount = game.pot // len(active_players)
            for player in active_players:
                player.chips += split_amount
            game.pot = 0

        # End the game
        await self.store.end_game(game.game_id, [p.id for p in active_players], None)

    async def get_game_state(self, game_id: str) -> Optional[GameState]:
        """Get game state with additional computed fields"""
        return self.store.get_game(game_id)

    async def get_available_actions(self, game_id: str, player_id: str) -> List[str]:
        """Get available actions for a player"""
        game = self.store.get_game(game_id)
        if not game:
            return []

        player = next((p for p in game.players if p.id == player_id), None)
        if not player or player.status == PlayerStatus.FOLDED:
            return []

        actions = []
        call_amount = game.current_bet - player.current_bet

        if call_amount == 0:
            actions.extend(["check", "raise"])
        else:
            actions.extend(["fold", "call"])
            if player.chips > call_amount:
                actions.append("raise")

        if player.chips > 0:
            actions.append("all_in")

        return actions

    def update_behavior(self, behavior):
        aggressive_actions = sum(
            1
            for action in behavior.action_history
            if action.action_type in ["raise", "all_in"]
        )
        passive_actions = len(behavior.action_history) - aggressive_actions

        if aggressive_actions > passive_actions:
            behavior.aggression_modifier = min(1.5, behavior.aggression_modifier + 0.1)
        elif passive_actions > aggressive_actions:
            behavior.aggression_modifier = max(0.5, behavior.aggression_modifier - 0.1)
        else:
            # Gradually return to baseline
            if behavior.aggression_modifier > 1.0:
                behavior.aggression_modifier = max(
                    1.0, behavior.aggression_modifier - 0.05
                )
            elif behavior.aggression_modifier < 1.0:
                behavior.aggression_modifier = min(
                    1.0, behavior.aggression_modifier + 0.05
                )
        # type: ignore[unreachable]
