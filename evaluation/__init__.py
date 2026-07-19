"""DeepEval-based evaluation framework for the QA Expert Agent.

This package measures the agent; it never orchestrates it. The only module
that imports qa_agent is runners.agent_runner (the SUT bridge). qa_agent
never imports anything from here. See ARCHITECTURE.md Part 2.
"""
