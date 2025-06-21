import random
from typing import List, Dict, Any, Optional, Tuple
from ...models.game_models import (
    GameState,
    Player,
    PlayerAction,
    ActionType,
    GamePhase,
    Card,
    HandRank,
    HandRankType,
    PlayerStatus,
)
from ...models.agent_models import AgentMemory
from ...store.game_store import game_store


class PokerEngine:
    """Core poker game engine with hand evaluation and game logic."""

    def __init__(self) -> None:
        """Initialize the poker engine with a fresh deck."""
        self.deck: List[Card] = []
        self._initialize_deck()

    def _initialize_deck(self) -> None:
        """Initialize a standard 52-card deck."""
        suits = ["hearts", "diamonds", "clubs", "spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        self.deck = []
        for suit in suits:
            for i, rank in enumerate(ranks):
                self.deck.append(Card(suit=suit, rank=rank, value=values[i]))

    def shuffle_deck(self) -> None:
        """Shuffle the deck."""
        random.shuffle(self.deck)

    def deal_cards(self, num_players: int) -> List[List[Card]]:
        """Deal hole cards to players.

        Args:
            num_players: Number of players to deal cards to.

        Returns:
            List of hole card hands, one for each player.
        """
        if len(self.deck) < num_players * 2:
            self._initialize_deck()
            self.shuffle_deck()

        hands = []
        for _ in range(num_players):
            hand = [self.deck.pop(), self.deck.pop()]
            hands.append(hand)

        return hands

    def deal_community_cards(self, count: int) -> List[Card]:
        """Deal community cards (flop, turn, river).

        Args:
            count: Number of community cards to deal.

        Returns:
            List of community cards dealt.
        """
        if len(self.deck) < count:
            self._initialize_deck()
            self.shuffle_deck()

        cards = []
        for _ in range(count):
            cards.append(self.deck.pop())

        return cards

    def evaluate_hand(
        self, hole_cards: List[Card], community_cards: List[Card]
    ) -> HandRank:
        """Evaluate the best 5-card hand from hole and community cards.

        Args:
            hole_cards: Player's hole cards.
            community_cards: Community cards on the board.

        Returns:
            HandRank representing the best possible hand.
        """
        all_cards = hole_cards + community_cards

        # Get all possible 5-card combinations
        best_hand = self._get_best_hand(all_cards)

        return best_hand

    def _get_best_hand(self, cards: List[Card]) -> HandRank:
        """Get the best 5-card hand from a list of cards.

        Args:
            cards: List of cards to evaluate.

        Returns:
            HandRank representing the best 5-card hand.
        """
        if len(cards) < 5:
            # Not enough cards for a valid hand
            return HandRank(
                rank=HandRankType.HIGH_CARD,
                value=1,
                cards=cards[:5] if len(cards) >= 5 else cards,
                kickers=[],
            )

        # Get all 5-card combinations
        from itertools import combinations

        five_card_combinations = list(combinations(cards, 5))

        best_hand = None
        best_value = 0

        for combo in five_card_combinations:
            hand_rank = self._evaluate_five_cards(list(combo))
            if hand_rank.value > best_value:
                best_value = hand_rank.value
                best_hand = hand_rank

        return best_hand or HandRank(
            rank=HandRankType.HIGH_CARD, value=1, cards=cards[:5], kickers=[]
        )

    def _evaluate_five_cards(self, cards: List[Card]) -> HandRank:
        """Evaluate a 5-card hand.

        Args:
            cards: Exactly 5 cards to evaluate.

        Returns:
            HandRank representing the hand type and value.
        """
        if len(cards) != 5:
            return HandRank(rank=HandRankType.INVALID, value=0, cards=cards, kickers=[])

        # Sort cards by value (descending)
        cards.sort(key=lambda x: x.value, reverse=True)

        # Check for each hand type from highest to lowest
        if self._is_royal_flush(cards):
            return HandRank(
                rank=HandRankType.ROYAL_FLUSH, value=10, cards=cards, kickers=[]
            )
        elif self._is_straight_flush(cards):
            return HandRank(
                rank=HandRankType.STRAIGHT_FLUSH, value=9, cards=cards, kickers=[]
            )
        elif self._is_four_of_a_kind(cards):
            return HandRank(
                rank=HandRankType.FOUR_OF_A_KIND, value=8, cards=cards, kickers=[]
            )
        elif self._is_full_house(cards):
            return HandRank(
                rank=HandRankType.FULL_HOUSE, value=7, cards=cards, kickers=[]
            )
        elif self._is_flush(cards):
            return HandRank(rank=HandRankType.FLUSH, value=6, cards=cards, kickers=[])
        elif self._is_straight(cards):
            return HandRank(
                rank=HandRankType.STRAIGHT, value=5, cards=cards, kickers=[]
            )
        elif self._is_three_of_a_kind(cards):
            return HandRank(
                rank=HandRankType.THREE_OF_A_KIND, value=4, cards=cards, kickers=[]
            )
        elif self._is_two_pair(cards):
            return HandRank(
                rank=HandRankType.TWO_PAIR, value=3, cards=cards, kickers=[]
            )
        elif self._is_one_pair(cards):
            return HandRank(
                rank=HandRankType.ONE_PAIR, value=2, cards=cards, kickers=[]
            )
        else:
            return HandRank(
                rank=HandRankType.HIGH_CARD, value=1, cards=cards, kickers=[]
            )

    def _is_royal_flush(self, cards: List[Card]) -> bool:
        """Check if cards form a royal flush."""
        return self._is_straight_flush(cards) and cards[0].value == 14  # Ace high

    def _is_straight_flush(self, cards: List[Card]) -> bool:
        """Check if cards form a straight flush."""
        return self._is_flush(cards) and self._is_straight(cards)

    def _is_four_of_a_kind(self, cards: List[Card]) -> bool:
        """Check if cards form four of a kind."""
        values = [card.value for card in cards]
        for value in set(values):
            if values.count(value) == 4:
                return True
        return False

    def _is_full_house(self, cards: List[Card]) -> bool:
        """Check if cards form a full house."""
        values = [card.value for card in cards]
        unique_values = list(set(values))
        if len(unique_values) == 2:
            count1 = values.count(unique_values[0])
            count2 = values.count(unique_values[1])
            return (count1 == 3 and count2 == 2) or (count1 == 2 and count2 == 3)
        return False

    def _is_flush(self, cards: List[Card]) -> bool:
        """Check if cards form a flush."""
        suit = cards[0].suit
        return all(card.suit == suit for card in cards)

    def _is_straight(self, cards: List[Card]) -> bool:
        """Check if cards form a straight."""
        values = [card.value for card in cards]
        values.sort()

        # Check for regular straight
        for i in range(len(values) - 1):
            if values[i + 1] - values[i] != 1:
                break
        else:
            return True

        # Check for Ace-low straight (A, 2, 3, 4, 5)
        if values == [2, 3, 4, 5, 14]:
            return True

        return False

    def _is_three_of_a_kind(self, cards: List[Card]) -> bool:
        """Check if cards form three of a kind."""
        values = [card.value for card in cards]
        for value in set(values):
            if values.count(value) == 3:
                return True
        return False

    def _is_two_pair(self, cards: List[Card]) -> bool:
        """Check if cards form two pair."""
        values = [card.value for card in cards]
        pairs = 0
        for value in set(values):
            if values.count(value) == 2:
                pairs += 1
        return pairs == 2

    def _is_one_pair(self, cards: List[Card]) -> bool:
        """Check if cards form one pair."""
        values = [card.value for card in cards]
        for value in set(values):
            if values.count(value) == 2:
                return True
        return False

    async def start_new_game(self, room_id: str) -> Optional[GameState]:
        """Start a new poker game in a room.

        Args:
            room_id: ID of the room to start the game in.

        Returns:
            GameState if successful, None otherwise.
        """
        room = game_store.get_room(room_id)
        if not room or not room.can_start_game():
            return None

        # Create new game state
        game = await game_store.create_game(room_id)
        if not game:
            return None

        # Initialize deck and deal cards
        self._initialize_deck()
        self.shuffle_deck()

        # Deal hole cards to players
        hole_cards = self.deal_cards(len(game.players))
        for i, player in enumerate(game.players):
            player.hole_cards = hole_cards[i]
            player.current_bet = 0
            player.status = PlayerStatus.ACTIVE

        # Set up blinds
        self._setup_blinds(game)

        # Set game phase
        game.phase = GamePhase.PRE_FLOP
        game.started_at = None  # Will be set when first action is made

        return game

    def _setup_blinds(self, game: GameState) -> None:
        """Set up small and big blinds for the game.

        Args:
            game: Game state to set up blinds for.
        """
        if len(game.players) < 2:
            return

        # Small blind
        sb_player = game.players[game.dealer_index]
        sb_amount = min(game.small_blind, sb_player.chips)
        sb_player.current_bet = sb_amount
        sb_player.chips -= sb_amount
        game.pot += sb_amount

        # Big blind
        bb_index = (game.dealer_index + 1) % len(game.players)
        bb_player = game.players[bb_index]
        bb_amount = min(game.big_blind, bb_player.chips)
        bb_player.current_bet = bb_amount
        bb_player.chips -= bb_amount
        game.pot += bb_amount

        game.current_bet = bb_amount
        game.min_raise = bb_amount

    def advance_game_phase(self, game: GameState) -> None:
        """Advance the game to the next phase.

        Args:
            game: Game state to advance.
        """
        match game.phase:
            case GamePhase.PRE_FLOP:
                game.phase = GamePhase.FLOP
                # Deal flop (3 cards)
                game.community_cards = self.deal_community_cards(3)
            case GamePhase.FLOP:
                game.phase = GamePhase.TURN
                # Deal turn (1 card)
                game.community_cards.extend(self.deal_community_cards(1))
            case GamePhase.TURN:
                game.phase = GamePhase.RIVER
                # Deal river (1 card)
                game.community_cards.extend(self.deal_community_cards(1))
            case GamePhase.RIVER:
                game.phase = GamePhase.SHOWDOWN
                self._determine_winner(game)
            case _:
                # Handle any other phases
                pass

        # Reset betting for new phase
        game.current_bet = 0
        game.min_raise = game.big_blind
        for player in game.players:
            player.current_bet = 0

    def _determine_winner(self, game: GameState) -> None:
        """Determine the winner(s) of the hand.

        Args:
            game: Game state to determine winner for.
        """
        active_players = [p for p in game.players if p.status == "active"]

        if len(active_players) == 1:
            # Only one player left, they win
            game.winners = [active_players[0].id]
            return

        # Evaluate hands for all active players
        player_hands = []
        for player in active_players:
            hand_rank = self.evaluate_hand(player.hole_cards, game.community_cards)
            player_hands.append((player, hand_rank))

        # Find the best hand
        best_hand_value = max(hand.value for _, hand in player_hands)
        winners = [
            player for player, hand in player_hands if hand.value == best_hand_value
        ]

        game.winners = [player.id for player in winners]
        game.winning_hand = player_hands[0][1]  # Store the winning hand rank

    def is_game_complete(self, game: GameState) -> bool:
        """Check if the current betting round is complete.

        Args:
            game: Game state to check.

        Returns:
            True if betting round is complete, False otherwise.
        """
        active_players = [p for p in game.players if p.status == "active"]

        if len(active_players) <= 1:
            return True

        # Check if all active players have bet the same amount
        bet_amounts = [p.current_bet for p in active_players]
        return len(set(bet_amounts)) == 1 and bet_amounts[0] == game.current_bet


# Global poker engine instance
poker_engine = PokerEngine()

# Import datetime for the start_new_game method
from datetime import datetime
