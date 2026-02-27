"""
Enterprise Data Sanitization Platform
Deterministic State Machine
"""
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

import sys
import os
# Ensure core can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.exception_types import StateMachineError
from core.logging_engine import wipe_logger

class WipeState(Enum):
    """Strict states for the wipe operation."""
    IDLE = auto()
    DEVICE_VALIDATED = auto()
    LOCKED = auto()
    PRE_HASHED = auto()
    OVERWRITING = auto()
    VERIFYING = auto()
    COMPLETED = auto()
    ERROR = auto()
    SAFE_RELEASE = auto()

class WipeStateMachine:
    """
    Deterministic state machine to govern the wipe process.
    Ensures operations only occur in the correct sequence.
    """
    def __init__(self):
        self._current_state = WipeState.IDLE
        
        # Define valid transitions
        self._transitions: Dict[WipeState, List[WipeState]] = {
            WipeState.IDLE: [WipeState.DEVICE_VALIDATED, WipeState.ERROR],
            WipeState.DEVICE_VALIDATED: [WipeState.LOCKED, WipeState.ERROR, WipeState.SAFE_RELEASE],
            WipeState.LOCKED: [WipeState.PRE_HASHED, WipeState.ERROR, WipeState.SAFE_RELEASE],
            WipeState.PRE_HASHED: [WipeState.OVERWRITING, WipeState.ERROR, WipeState.SAFE_RELEASE],
            WipeState.OVERWRITING: [WipeState.VERIFYING, WipeState.ERROR, WipeState.SAFE_RELEASE],
            WipeState.VERIFYING: [WipeState.COMPLETED, WipeState.ERROR, WipeState.SAFE_RELEASE],
            WipeState.COMPLETED: [WipeState.SAFE_RELEASE],
            WipeState.ERROR: [WipeState.SAFE_RELEASE],
            WipeState.SAFE_RELEASE: [WipeState.IDLE]
        }

    @property
    def current_state(self) -> WipeState:
        return self._current_state

    def transition_to(self, new_state: WipeState) -> None:
        """
        Attempt to transition to a new state.
        
        Args:
            new_state: The target state.
            
        Raises:
            StateMachineError: If the transition is invalid.
        """
        valid_next_states = self._transitions.get(self._current_state, [])
        
        if new_state not in valid_next_states:
            error_msg = f"Invalid state transition attempted: {self._current_state.name} -> {new_state.name}"
            wipe_logger.error(error_msg)
            
            # If we are trying to go to an error or safe release state, we should force it
            # to prevent getting stuck in a dangerous state, but still log the violation.
            if new_state in (WipeState.ERROR, WipeState.SAFE_RELEASE):
                wipe_logger.warning(f"Forcing emergency transition to {new_state.name}")
                self._current_state = new_state
                return
                
            raise StateMachineError(error_msg)
            
        wipe_logger.info(f"State transition: {self._current_state.name} -> {new_state.name}")
        self._current_state = new_state

    def assert_state(self, expected_state: WipeState) -> None:
        """
        Assert that the machine is in a specific state.
        
        Args:
            expected_state: The state the machine must be in.
            
        Raises:
            StateMachineError: If the machine is not in the expected state.
        """
        if self._current_state != expected_state:
            raise StateMachineError(f"Expected state {expected_state.name}, but currently in {self._current_state.name}")
