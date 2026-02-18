"""
Instruction Validation Module - Phase 6.3

Validates AI worker instruction documents against 10-point framework.
Provides early quality gates before expensive LLM execution.
"""

from instruction_validation.instruction_composite_validator import InstructionCompositeValidator

__all__ = ["InstructionCompositeValidator"]
