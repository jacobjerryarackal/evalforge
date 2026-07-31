import asyncio
import os
from dotenv import load_dotenv
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.judges import FaithfulnessJudge
from src.domain.entities.dataset import GoldenTestCase
from src.domain.entities.trajectory import Trajectory, Step

async def main():
    load_dotenv()
    print("GEMINI_API_KEY preset:", bool(os.getenv("GEMINI_API_KEY")))
    
    # Initialize provider in REAL mode
    provider = GeminiProvider(mock_mode=False)
    print(f"Provider model: {provider.model_name}, Mock mode: {provider.mock_mode}")
    
    # Set up Faithfulness Judge
    judge = FaithfulnessJudge(provider=provider)
    print(f"Initialized judge: {judge.name}")
    
    # Create a realistic test case and trajectory
    case = GoldenTestCase(
        case_id="test_case_real",
        input_query="Book flight from JFK to LAX",
        retrieved_context="Flight UA100 from JFK to LAX is available for $300 on August 1st.",
        expected_answer="Booked UA100 for $300."
    )
    
    trajectory = Trajectory()
    trajectory.add_step(
        Step(
            step_number=1,
            thought="Searching for flights...",
            response="I have booked flight UA100 from JFK to LAX for $300."
        )
    )
    
    print("Calling Faithfulness Judge (this will perform a live Gemini API call)...")
    try:
        res = await judge.evaluate(case, trajectory)
        print("Success! Judge Result:")
        print(f"  Metric Name: {res.metric_name}")
        print(f"  Score: {res.score}")
        print(f"  Reasoning: {res.reasoning}")
        print(f"  Metadata: {res.metadata}")
    except Exception as e:
        print("Verification failed with error:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
